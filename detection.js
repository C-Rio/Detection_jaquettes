
let imgElement = document.getElementById('imageSrc');
let inputElement = document.getElementById('fileInput');
inputElement.addEventListener('change', (e) => { imgElement.src = URL.createObjectURL(e.target.files[0]); }, false);

imgElement.onload = function () {
    let mat = cv.imread(imgElement);
    maintain_aspect_ratio_resize(mat, mat, width = 750);

    let mat_gray = new cv.Mat();
    cv.cvtColor(mat, mat_gray, cv.COLOR_RGBA2GRAY, 0);

    let mat_gray_resized = new cv.Mat();
    maintain_aspect_ratio_resize(mat_gray, mat_gray_resized, width = 750);
    mat_gray.delete()


    let mat_gray_resized_blur = new cv.Mat();
    cv.medianBlur(mat_gray_resized, mat_gray_resized_blur, 15);
    mat_gray_resized.delete()

    let img_h = mat_gray_resized_blur.rows;
    let img_w = mat_gray_resized_blur.cols;

    let margin_x = Math.floor(img_w * 0.01)
    let margin_y = Math.floor(img_h * 0.01)


    let mat_gray_resized_blur_thresh = new cv.Mat();
    cv.adaptiveThreshold(mat_gray_resized_blur, mat_gray_resized_blur_thresh, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 11, 2);
    mat_gray_resized_blur.delete()


    let mat_gray_resized_blur_thresh_inv = new cv.Mat();
    cv.bitwise_not(mat_gray_resized_blur_thresh, mat_gray_resized_blur_thresh_inv);
    mat_gray_resized_blur_thresh.delete()


    let blue = new cv.Scalar(0, 0, 255, 1)
    let lines = new cv.Mat();
    cv.HoughLinesP(mat_gray_resized_blur_thresh_inv, lines, 1, Math.PI / 180, 250, 50, 20);
    mat_gray_resized_blur_thresh_inv.delete()

    // If no lines have been found, display original image
    if (lines.rows == 0) {
        cv.imshow('canvasOutput', mat);
        return null;
    }

    let filtered_line = [];

    // draw lines
    for (let i = 0; i < lines.rows; ++i) {
        let startPoint = new cv.Point(lines.data32S[i * 4], lines.data32S[i * 4 + 1]);
        let endPoint = new cv.Point(lines.data32S[i * 4 + 2], lines.data32S[i * 4 + 3]);

        if (is_line_outside_margin(startPoint, endPoint, margin_x, margin_y, img_w, img_h)) {
            cv.line(mat, startPoint, endPoint, blue);
            filtered_line.push(lines.data32S[i * 4], lines.data32S[i * 4 + 1], lines.data32S[i * 4 + 2], lines.data32S[i * 4 + 3]);
        }
    }

    console.log("filtered line len " + filtered_line.length)
    console.log("filtered line", filtered_line)

    // If almost all lines have been filtered, display original image
    if (filtered_line.length < 8) {
        cv.imshow('canvasOutput', mat);
        return null;
    }

    // For example: let mat = cv.matFromArray(2, 2, cv.CV_8UC1, [1, 2, 3, 4]);
    let mat2 = cv.matFromArray(filtered_line.length / 2, 2, cv.CV_32S, filtered_line);
    // console.log(mat2.data32S)

    var contours = new cv.MatVector();
    contours.push_back(mat2)


    var hull = new cv.Mat();
    var cnt = contours.get(0);
    cv.convexHull(cnt, hull, false, true);

    // console.log(hull.data32S)


    let rect_contours = simplify_contour(hull)

    // cv.drawContours(mat, hulls, -1, blue, 3);
    console.log("rect_contours", rect_contours.data32S)
    console.log("rect_contours len", rect_contours.data32S.length)

    lines_len = []
    lines_coords = []
    for (let i = 0; i < rect_contours.data32S.length - 2; i = i + 2) {
        x1 = rect_contours.data32S[i]
        y1 = rect_contours.data32S[i + 1]
        x2 = rect_contours.data32S[i + 2]
        y2 = rect_contours.data32S[i + 3]
        lines_len.push(line_length(x1, y1, x2, y2))
        lines_coords.push(x1, y1, x2, y2)
    }
    x1 = rect_contours.data32S[rect_contours.data32S.length - 2];
    y1 = rect_contours.data32S[rect_contours.data32S.length - 1];
    x2 = rect_contours.data32S[0];
    y2 = rect_contours.data32S[1];
    lines_len.push(line_length(x1, y1, x2, y2));
    lines_coords.push(x1, y1, x2, y2)

    console.log("lines_len", lines_len)

    // S'il y a moins de 4 lignes, afficher l'image d'origine
    if (lines_len.length < 4) {
        cv.imshow('canvasOutput', mat);
        return null;
    }


    let topValues = [...lines_len].sort((a, b) => b - a).slice(0, 4);
    console.log("topValues", topValues);
    let topIndexes = []
    let topCoords = []
    for (let i = 0; i < 4; i++) {
        topIndexes.push(lines_len.findIndex(len => len == topValues[i]))
        topCoords.push(rect_contours.data32S[topIndexes[i] * 2], rect_contours.data32S[topIndexes[i] * 2 + 1])

        if (topIndexes[i] == lines_len.length - 1)
            topCoords.push(rect_contours.data32S[0], rect_contours.data32S[1])
        else
            topCoords.push(rect_contours.data32S[topIndexes[i] * 2 + 2], rect_contours.data32S[topIndexes[i] * 2 + 3])
    }
    console.log("topIndexes", topIndexes);
    console.log("topCoords", topCoords);


    let intersections = []
    for (let i = 0; i < 16; i = i + 4) {
        for (let j = i + 4; j < 16; j = j + 4) {
            // Deux points de la droite 1
            Ax1 = topCoords[i]
            Ay1 = topCoords[i + 1]
            Ax2 = topCoords[i + 2]
            Ay2 = topCoords[i + 3]

            // Deux points de la droite 2
            Bx1 = topCoords[j]
            By1 = topCoords[j + 1]
            Bx2 = topCoords[j + 2]
            By2 = topCoords[j + 3]

            // Calcul des equations des deux droites
            eq1 = equation_droite(Ax1, Ay1, Ax2, Ay2)
            eq2 = equation_droite(Bx1, By1, Bx2, By2)

            // Pour déterminer les intersections, on vérifie que les droite ne sont pas parallèle
            if (!are_lines_parallel(eq1, eq2)) {
                //  En cas de droite verticale
                if (eq1 == 'NA') {
                    x_int = Ax1
                    y_int = eq2[0] * Ax1 + eq2[1]
                }
                else if (eq2 == 'NA') {
                    x_int = Bx1
                    y_int = eq1[0] * Bx1 + eq1[1]
                }
                else {
                    inter = point_intersection(eq1, eq2)
                    x_int = inter[0]
                    y_int = inter[1]
                }
                //  On ne conserve que les intersections qui se situent dans l'image
                if (inter[0] >= 0 && inter[1] >= 0 && inter[0] <= img_w && inter[1] <= img_h)
                    intersections.push(Math.floor(inter[0]), Math.floor(inter[1]))
            }
        }
    }

    console.log("intersections", intersections);

    if (intersections.length != 8) {
        let rect = cv.boundingRect(rect_contours);
        let rectangleColor = new cv.Scalar(255, 0, 0);

        let point1 = new cv.Point(rect.x, rect.y);
        let point2 = new cv.Point(rect.x + rect.width, rect.y + rect.height)

        cv.rectangle(mat, point1, point2, rectangleColor, 2,);
        cv.imshow('canvasOutput', mat);
        return null;

        // return image[y: y + h, x: x + w]
    }
    else {
        let mat3 = cv.matFromArray(intersections.length / 2, 2, cv.CV_32S, intersections);
        console.log(mat3.data32S)

        // var contours2 = new cv.MatVector();
        // contours2.push_back(mat3)


        var hull2 = new cv.Mat();
        // var cnt2 = contours.get(0);
        cv.convexHull(mat3, hull2, false, true);
        console.log("hull2", hull2.data32S)

        let point_top = hull2.clone();

    }



    // points_top = np.copy(hull5)
    // points_bottom = np.empty((0, 2), dtype = int)

    // points_bottom_ind = np.argmax(points_top[:, 1], axis = 0)
    // points_bottom = np.vstack((points_bottom, points_top[points_bottom_ind]))
    // points_top = np.delete(points_top, points_bottom_ind, 0)

    // points_bottom_ind = np.argmax(points_top[:, 1], axis = 0)
    // points_bottom = np.vstack((points_bottom, points_top[points_bottom_ind]))
    // points_top = np.delete(points_top, points_bottom_ind, 0)


    /* let green = new cv.Scalar(0, 255, 0);
        let contourID0 = 10;
        cv.drawContours(cv_src, contours, contourID0, green, 1, cv.LINE_8, hierarchy, 100)
        
        for (let i = 0; i < contours.size(); ++i) {
          let color = new cv.Scalar(Math.round(Math.random() * 255), Math.round(Math.random() * 255),
                                    Math.round(Math.random() * 255));
          cv.drawContours(cv_src, contours, i, color, 3, cv.LINE_8, hierarchy, 100);
          } */

    // cv.imshow('canvasOutput', mat);



    // console.log(lines.data32S[4])
    // console.log(lines.data32S.length)





    // cv.imshow('canvasOutput', thresh);

    // mat_gray_resized_blur_thresh.delete()
};


function maintain_aspect_ratio_resize(image, dst, width = null, height = null, inter = cv.INTER_AREA) {

    // Grab the image size and initialize dimensions
    let dim = null;
    let h = image.rows;
    let w = image.cols;
    // (h, w) = image.shape[: 2]

    // Return original image if no need to resize
    if (width === null && height === null)
        return image;

    // We are resizing height if width is none
    if (width === null) {
        // Calculate the ratio of the height and construct the dimensions
        let r = height / h;
        dim = new cv.Size(Math.floor(w * r), height);
    }
    // We are resizing width if height is none
    else {
        //  Calculate the ratio of the width and construct the dimensions
        let r = width / w;
        dim = new cv.Size(width, Math.floor(h * r));
    }

    // Resize the image
    cv.resize(image, dst, dim, 0, 0, inter);
}

function is_line_outside_margin(point1, point2, margin_x, margin_y, img_w, img_h) {

    if (point1.x < margin_x || point2.x < margin_x || point1.y < margin_y || point2.y < margin_y || point1.x > img_w - margin_x || point2.x > img_w - margin_x || point1.y > img_h - margin_y || point2.y > img_h - margin_y)
        return false;

    else
        return true;
}

function simplify_contour(contour, n_corners = 6) {

    // Binary searches best`epsilon` value to force contour
    // approximation contain exactly`n_corners` points.

    // : param contour: OpenCV2 contour.
    // : param n_corners: Number of corners(points) the contour must contain.

    // : returns: Simplified contour in successful case.Otherwise returns initial contour.

    let n_iter = 0;
    let max_iter = 100;

    let lb = 0.0
    let ub = 1.0

    while (true) {
        n_iter += 1
        if (n_iter > max_iter)
            return contour

        k = (lb + ub) / 2
        eps = k * cv.arcLength(contour, true)
        let approx = new cv.Mat();
        cv.approxPolyDP(contour, approx, eps, true)

        if (approx.data32S.length > 2 * n_corners)
            lb = (lb + ub) / 2
        else if (approx.data32S.length < 2 * n_corners)
            ub = (lb + ub) / 2
        else
            return approx
    }
}

function line_length(x1, y1, x2, y2) {
    return Math.pow(Math.pow(x1 - x2, 2) + Math.pow(y1 - y2, 2), 1 / 2)
}


function slope(x1, y1, x2, y2) {
    if (x2 != x1)
        return ((y2 - y1) / (x2 - x1))
    else
        return 'NA'
}


function equation_droite(x1, y1, x2, y2) {
    pente = slope(x1, y1, x2, y2)
    if (pente != 'NA') {
        ordonnee_origine = y1 - pente * x1
        return [pente, ordonnee_origine]
    }
    else
        return 'NA'
}


function are_lines_parallel(droite1, droite2) {
    if (droite1[0] == droite2[0] || (droite1 == 'NA' && droite2 == 'NA'))
        return true
    else
        return false
}

function point_intersection(droite1, droite2) {
    if (droite1 != 'NA' && droite2 != 'NA') {
        x_int = (droite2[1] - droite1[1]) / (droite1[0] - droite2[0])
        y_int = droite1[0] * x_int + droite1[1]
        return [x_int, y_int]
    }
    else
        return 'NA'
}



function getMaxOfArray(numArray) {
    return Math.max.apply(null, numArray);
}

function onOpenCvReady() {
    document.getElementById('status').innerHTML = 'OpenCV.js is ready.';
}


