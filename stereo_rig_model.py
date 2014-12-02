import cv2
import numpy as np
import StringIO


#############
# CONSTANTS #
#############

# FLANN matching variables
FLANN_INDEX_KDTREE = 0
TREES = 5
CHECKS = 100
KNN_ITERS = 2
LOWE_RATIO = 0.8
# The header for a PLY point cloud
PLY_HEADER = '''ply
format ascii 1.0
element vertex %(vert_num)d
property float x
property float y
property float z
property uchar red
property uchar green
property uchar blue
end_header
'''


###########
# HELPERS #
###########

def point_cloud(disparity_image, image_left, focal_length):
    """Create a point cloud from a disparity image and a focal length.
        Arguments:
        disparity_image: disparities in pixels.
        image_left: BGR-format left stereo image, to color the points.
        focal_length: the focal length of the stereo camera, in pixels.
        Returns:
        A string containing a PLY point cloud of the 3D locations of the
        pixels, with colors sampled from left_image. You may filter low-
        disparity pixels or noise pixels if you choose.
        """
    h, w = image_left.shape[:2]
    Q = np.float32([[1, 0,  0, w / 2],
                    [0, -1,  0,  h / 2],  # turn points 180 deg around x-axis,
                    [0, 0, focal_length,  0],  # so that y-axis looks up
                    [0, 0,  0,  1]])
                    
    # reproject image points to 3D space, compute the colors
    points = cv2.reprojectImageTo3D(disparity_image, Q)
    colors = cv2.cvtColor(image_left, cv2.COLOR_BGR2RGB)
    mask = disparity_image > disparity_image.min()
    out_points = points[mask]
    out_colors = colors[mask]
    
    # write PLY string data to StringIO object and return the contents
    cloud = StringIO.StringIO()
    verts = np.hstack([out_points, out_colors])
    cloud.write(PLY_HEADER % dict(vert_num=len(verts)))
    np.savetxt(cloud, verts, '%f %f %f %d %d %d')
    
    return cloud.getvalue()


def get_stereo_depth(left_video, right_video):
    map_1_left = np.load("test_data/map_1_left.npy")
    map_2_left = np.load("test_data/map_2_left.npy")
    map_1_right = np.load("test_data/map_1_right.npy")
    map_2_right = np.load("test_data/map_2_right.npy")

    image_selected = False

    # StereoSGBM values
    minDisparity = 10
    numDisparities = 128
    SADWindowSize = 9
    P1 = 8 * 3 * 9 * 9
    P2 = 32 * 3 * 9 * 9
    disp12MaxDiff = -1

    # Block matcher
    stereo = cv2.StereoSGBM(minDisparity, numDisparities, SADWindowSize,
                            P1, P2, disp12MaxDiff)

    ret_left, frame_left_original = left_video.read()
    ret_right, frame_right_original = right_video.read()
    while ret_left is True and ret_right is True and image_selected is False:
        frame_left_gray = cv2.cvtColor(frame_left_original, cv2.COLOR_BGR2GRAY)
        frame_right_gray = cv2.cvtColor(frame_right_original, cv2.COLOR_BGR2GRAY)
        frame_left_gray_remapped = cv2.remap(frame_left_gray, map_1_left, map_2_left, cv2.INTER_LINEAR)
        frame_right_gray_remapped = cv2.remap(frame_right_gray, map_1_right, map_2_right, cv2.INTER_LINEAR)
        frame_left_color_remapped = cv2.remap(frame_left_original, map_1_left, map_2_left, cv2.INTER_LINEAR)
        disparity = stereo.compute(frame_left_gray_remapped,
                                   frame_right_gray_remapped).astype(np.float32) / 16
        disparity = np.uint8(disparity)
        cv2.imshow('frame_left', frame_left_gray_remapped)
        cv2.imshow('frame_right', frame_right_gray_remapped)
        cv2.imshow('disparity', disparity)
        k = cv2.waitKey(1) & 0xFF
        if k == ord('q'):
            image_selected = True
        ret_left, frame_left_original = left_video.read()
        ret_right, frame_right_original = right_video.read()

    cv2.imwrite("test_data/disparity.jpg", disparity)
    pc = point_cloud(disparity, frame_left_color_remapped, 10)

    # Destroy all windows
    cv2.destroyAllWindows()

    with open("test_data/pc.ply", 'w') as f:
        f.write(pc)


########
# MAIN #
########

def main():
    # Open the left and right streams
    left_video = cv2.VideoCapture(1)
    right_video = cv2.VideoCapture(2)
    get_stereo_depth(left_video, right_video)

if __name__ == '__main__':
    main()
