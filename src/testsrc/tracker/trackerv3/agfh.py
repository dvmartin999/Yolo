from collections import Counter
import numpy as np
import cv2


def Give_boundingbox_coor_class(bboxes):
    x1=[] # Top left x-coor
    y1=[] # Top left y-coor
    x2=[] # Bottom right x-coor
    y2=[] # Bottom right y-coor
    Score=[] # Class probabilities times objectness score
    C=[] # Class
    for i in range(len(bboxes)):
        boundingbox=bboxes[i]
        boundingbox_int=boundingbox.astype(int)
        x1.append(boundingbox_int[0])
        y1.append(boundingbox_int[1])
        x2.append(boundingbox_int[2])
        y2.append(boundingbox_int[3])
        Score.append(boundingbox[4])
        C.append(boundingbox_int[5])
    return x1, y1, x2, y2, Score, C

def k_means_depth(img,k=3,maxiter=1000,eps=0.1):
    imgre=img.reshape((-1,1)) # Flatten the image (pixels,1)
    imgre=np.float32(imgre) # cv2.kmeans needs float32
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,1000, 0.1)
    k=3 # Number of segmented regions
    _, label, center = cv2.kmeans(imgre, k, None, criteria, 100, cv2.KMEANS_RANDOM_CENTERS)
    #print(center)
    # Calculated average depth of object
    Sort=Counter(label.flatten()).most_common()
    #print(Sort)
    label_max=Sort[0][0]
    avg_depth=center[label_max][0]

    # For plotting of segmented image
    center = np.float64(center)
    res = center[label.flatten()] 
    img_seg = res.reshape((img.shape)) #Segmented image
    
    return avg_depth, img_seg

def Simple_Pinhole(P,D):
    '''
    Simple Pinhole Model to calculate physical position based on depth and pixel coordinates 
    for Zed2 left camera FullHD. Numeric.
    Assumed no rotation or translation
    #https://docs.opencv.org/2.4/modules/calib3d/doc/camera_calibration_and_3d_reconstruction.html
    Parameters:
        P: Position (Pixel)
        D: Depth (m)
        c: Pricipal point
        f: Focal length
        
fx=529.085
fy=528.38
cx=645.815
cy=376.6125
k1=-0.0396842
k2=0.00917941
k3=-0.0047467
p1=0.00010877
p2=0.000124303
    '''
    f = [529.085,528.38]
    c = [645.815,376.6125]
    R = [[0, 0, 1],[0, 1, 0], [-1 , 0, 0]] # Rotation around y axis

    xm = (P[0]-c[0])/f[0]
    ym = (P[1]-c[1])/f[1]

    x = xm*D
    y = ym*D

    #Lc = [[x],[y],[d]]

    #Gc = Lc*R 
    #print(Gc)   
    
    return x, y , D