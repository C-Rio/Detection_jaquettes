# import required libraries
import numpy as np
from cv2 import cv2
import os
import math as math


def slope(x1, y1, x2, y2):
    if x2 != x1:
        return ((y2 - y1) / (x2 - x1))
    else:
        return 'NA'


def simplify_contour(contour, n_corners=6):
    '''
    Binary searches best `epsilon` value to force contour
        approximation contain exactly `n_corners` points.

    :param contour: OpenCV2 contour.
    :param n_corners: Number of corners (points) the contour must contain.

    :returns: Simplified contour in successful case. Otherwise returns initial contour.
    '''
    n_iter, max_iter = 0, 100
    lb, ub = 0., 1.

    while True:
        n_iter += 1
        if n_iter > max_iter:
            return contour

        k = (lb + ub) / 2.
        eps = k * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, eps, True)

        if len(approx) > n_corners:
            lb = (lb + ub) / 2.
        elif len(approx) < n_corners:
            ub = (lb + ub) / 2.
        else:
            return approx


def equation_droite(x1, y1, x2, y2):
    pente = slope(x1, y1, x2, y2)
    if pente != 'NA':
        ordonnee_origine = y1 - pente * x1
        return (pente, ordonnee_origine)
    else:
        return 'NA'


def point_intersection(droite1, droite2):
    if droite1[0] != 'NA' and droite2 != 'NA':
        x_int = (droite2[1] - droite1[1]) / (droite1[0] - droite2[0])
        y_int = droite1[0] * x_int + droite1[1]
        return (x_int, y_int)
    else:
        return 'NA'


def line_length(point_a, point_b):
    return ((point_a[1] - point_b[1])**2 + (point_a[0] - point_b[0])**2)**(1 / 2)


def is_line_outside_margin(line, margin, img_dim):
    x1, y1, x2, y2 = line
    if (x1 < margin[1] or x2 < margin[1] or y1 < margin[0] or y2 < margin[0]
            or x1 > img_dim[1] - margin[1] or x2 > img_dim[1] - margin[1]
            or y1 > img_dim[0] - margin[0] or y2 > img_dim[0] - margin[0]):
        return False
    else:
        return True


def are_lines_parallel(droite1, droite2):
    if droite1 == droite2 or (droite1 == 'NA' and droite2 == 'NA'):
        return True
    else:
        return False


def lines_intersection_angle(droite1, droite2):
    if droite1 == 'NA':
        droite1 = (1000000000, None)

    if droite2 == 'NA':
        droite2 = (1000000000, None)

    angle = math.degrees(math.pi - abs(math.atan(droite1[0]) - math.atan(droite2[0])))
    return angle


def maintain_aspect_ratio_resize(image,
                                 width=None,
                                 height=None,
                                 inter=cv2.INTER_AREA):
    # Grab the image size and initialize dimensions
    dim = None
    (h, w) = image.shape[:2]

    # Return original image if no need to resize
    if width is None and height is None:
        return image

    # We are resizing height if width is none
    if width is None:
        # Calculate the ratio of the height and construct the dimensions
        r = height / float(h)
        dim = (int(w * r), height)
    # We are resizing width if height is none
    else:
        # Calculate the ratio of the width and construct the dimensions
        r = width / float(w)
        dim = (width, int(h * r))

    # Return the resized image
    return cv2.resize(image, dim, interpolation=inter)


def draw_contour(args_image):

    # Read images and does preprocessing (greyscale, Blur)
    # args_image = "Images/image2.png"
    image = cv2.imread(args_image)
    imageGrey = cv2.imread(args_image, 0)

    image = maintain_aspect_ratio_resize(image, width=750)
    imageGrey = maintain_aspect_ratio_resize(imageGrey, width=750)

    img_dim = np.delete(image.shape, 2)

    image2Grey = cv2.medianBlur(imageGrey, 15, 5)  # medianBlur 15, 5

    margin = (int(img_dim[0] * 0.01), int(img_dim[1] * 0.01))  # 0.03
    th3 = cv2.adaptiveThreshold(image2Grey, 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 11, 2)

    lines = np.squeeze(cv2.HoughLinesP(cv2.bitwise_not(th3),
                                       1,
                                       np.pi / 180,
                                       threshold=250,
                                       minLineLength=50,
                                       maxLineGap=20))

    # If no lines have been found, return original image
    if lines.shape[0] == 0:
        return image

    # filtered_line.shape = (:, 4)
    filtered_line = filter(lambda x: is_line_outside_margin(x, margin, img_dim), lines)
    filtered_line = np.asarray(list(filtered_line))

    # If all lines have been filtered, return original image
    if filtered_line.shape[0] == 0:
        return image

    # hough.shape = (:, 2)
    hough = np.reshape(filtered_line, (-1, 2))
    hull = np.squeeze(cv2.convexHull(hough))

    # rect_contour.shape = (:, 2)
    rect_contour = np.squeeze(simplify_contour(hull))
    # cv2.drawContours(image, [rect_contour], -1, (0, 255, 255), 4, cv2.LINE_4)

    # On calcule la longueur de chaque segment
    list3 = []
    for i in range(rect_contour.shape[0]-1):
        list3.append((line_length(rect_contour[i], rect_contour[i + 1]), (rect_contour[i], rect_contour[i + 1])))
    list3.append((line_length(rect_contour[rect_contour.shape[0]-1], rect_contour[0]), (rect_contour[rect_contour.shape[0]-1], rect_contour[0])))

    # S'il y a moins de 4 lignes, retourner l'image d'origine
    if len(list3) < 4:
        return image

    # On sélectionne les 4 lignes les plus longues
    max_coords = np.empty((0, 4))
    for i in range(4):
        index = list3.index(max(list3))
        line = np.concatenate((list3[index][1][0], list3[index][1][1]), axis=None)
        max_coords = np.vstack((max_coords, line))
        del list3[index]

    # print(max_coords)

    intersections = np.empty((0, 2), dtype=int)
    for i in range(len(max_coords)):
        for j in range(i + 1, len(max_coords)):

            # Deux points de la droite 1
            Ax1 = max_coords[i][0]
            Ay1 = max_coords[i][1]
            Ax2 = max_coords[i][2]
            Ay2 = max_coords[i][3]

            # Deux points de la droite 2
            Bx1 = max_coords[j][0]
            By1 = max_coords[j][1]
            Bx2 = max_coords[j][2]
            By2 = max_coords[j][3]

            # Calcul des equations des deux droites
            eq1 = equation_droite(Ax1, Ay1, Ax2, Ay2)
            eq2 = equation_droite(Bx1, By1, Bx2, By2)

            # Pour déterminer les intersections, on vérifie que les droite ne sont pas parallèle
            if not are_lines_parallel(eq1, eq2):
                # En cas de droite verticale
                if eq1 == 'NA':
                    x_int = Ax1
                    y_int = eq2[0] * Ax1 + eq2[1]
                elif eq2 == 'NA':
                    x_int = Bx1
                    y_int = eq1[0] * Bx1 + eq1[1]
                else:
                    x_int, y_int = point_intersection(eq1, eq2)

                # On ne conserve que les intersections qui se situent dans l'image
                if x_int >= 0 and y_int >= 0 and x_int <= img_dim[1] and y_int <= img_dim[0]:
                    # cv2.circle(image, (int(x_int), int(y_int)), 5, (255, 255, 255), 3)
                    intersections = np.vstack((intersections, np.array([int(x_int), int(y_int)])))

    if intersections.shape[0] != 4:
        x, y, w, h = cv2.boundingRect(rect_contour)
        # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
        return image[y:y+h, x:x+w]

    else:
        hull5 = np.squeeze(cv2.convexHull(intersections))
        points_top = np.copy(hull5)

        points_bottom = np.empty((0, 2), dtype=int)

        points_bottom_ind = np.argmax(points_top[:, 1], axis=0)
        points_bottom = np.vstack((points_bottom, points_top[points_bottom_ind]))
        points_top = np.delete(points_top, points_bottom_ind, 0)

        points_bottom_ind = np.argmax(points_top[:, 1], axis=0)
        points_bottom = np.vstack((points_bottom, points_top[points_bottom_ind]))
        points_top = np.delete(points_top, points_bottom_ind, 0)

        if points_bottom[0, 0] > points_bottom[1, 0]:
            points_bottom[[0, 1], :] = points_bottom[[1, 0], :]

        if points_top[0, 0] > points_top[1, 0]:
            points_top[[0, 1], :] = points_top[[1, 0], :]

        eq_left_line = equation_droite(points_bottom[0, 0], points_bottom[0, 1], points_top[0, 0], points_top[0, 1])
        eq_top_line = equation_droite(points_top[0, 0], points_top[0, 1], points_top[1, 0], points_top[1, 1])
        eq_right_line = equation_droite(points_top[1, 0], points_top[1, 1], points_bottom[1, 0], points_bottom[1, 1])
        eq_bottom_line = equation_droite(points_bottom[0, 0], points_bottom[0, 1], points_bottom[1, 0], points_bottom[1, 1])

        angle_top_left = lines_intersection_angle(eq_left_line, eq_top_line)
        angle_top_right = lines_intersection_angle(eq_top_line, eq_right_line)
        angle_bottom_right = lines_intersection_angle(eq_right_line, eq_bottom_line)
        angle_bottom_left = lines_intersection_angle(eq_bottom_line, eq_left_line)

        x, y, w, h = cv2.boundingRect(hull5)
        coords_dest = np.array([(x, y + h), (x, y), (x + w, y), (x + w, y + h)])

        if (abs(angle_top_left - angle_top_right) >= 30 or abs(angle_bottom_right - angle_bottom_left) >= 30):
            x, y, w, h = cv2.boundingRect(hull5)
            # cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            return image[y:y+h, x:x+w]

        else:
            # [bottom_left, top_left, top_right, bottom_right]
            coords_src = np.array([points_bottom[0, :], points_top[0, :], points_top[1, :], points_bottom[1, :]])

            homography = cv2.findHomography(coords_src, coords_dest, method=cv2.LMEDS)
            warped = cv2.warpPerspective(image, homography[0], (img_dim[1], img_dim[0]))

            return warped[y:y+h, x:x+w]


folder_src = "./Images/Images_src"
folder_dest = "./Images/Images_res"

for image in os.listdir(folder_src):
    img_drawn = draw_contour(os.path.join(folder_src, image))
    cv2.imwrite(os.path.join(folder_dest, image), img_drawn)

# img_drawn = draw_contour("./Images/image9.jpg")
# cv2.imshow("img_drawn", img_drawn)
# cv2.waitKey(0)
# cv2.imwrite(os.path.join(folder, "CONT_" + image), img_drawn)
