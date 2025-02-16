
def k_means_depth(img,k=3,max_iter=1000,tol=1e-4):
    imgre=img.reshape((-1,1)) # Flatten the image (pixel,1)
    imgre_scale = StandardScaler().fit_transform(imgre)
    KM_scale = KMeans(n_clusters=k, max_iter=max_iter, tol=tol, random_state=0).fit(imgre_scale)
    # Calculation of average depth
    label=KM_scale.labels_
    label=np.transpose(np.asarray([label])) # In order to concatenate
    Sort=Counter(label.flatten()).most_common() 
    label_max=Sort[0][0]
    a=np.concatenate((label,imgre),axis=1) # Put label and imgre side by side
    b=[] # Depth values from a which is at label_max
    for i in range(len(a)):
        if a[i,0]==label_max:
            b.append(a[i,1])
    avg_depth=np.mean(b)

    # For plotting segmented image
    center_scale = np.float64(KM_scale.cluster_centers_)
    res_scale = center_scale[label.flatten()] 
    img_seg_scale = res_scale.reshape((img.shape)) #Segmented image
    return avg_depth, img_seg_scale

def k_means_pointcloud_old(img,k=3,max_iter=1000,tol=1e-4):
    """
    img is point cloud image with three channels corresponding to x, y and z coordinate for each pixel.
    It must have the shape of [w,h,3]
    Coordinate system according to ZED2
    """
    imgre=img.reshape((-1,3)) # Flatten the image (pixel,3)
    imgre_wo_nan = imgre[~np.isnan(imgre).any(axis=1)] # remove rows with nan
    #imgre_wo_nan_and_inf = imgre_wo_nan[~np.isinf(imgre_wo_nan).any(axis=1)] # remove rows with inf
    imgre_scale = StandardScaler().fit_transform(imgre_wo_nan)
    KM_scale = KMeans(n_clusters=k, max_iter=max_iter, tol=tol, random_state=0).fit(imgre_scale)
    # Calculation of average depth
    label=KM_scale.labels_
    label=np.transpose(np.asarray([label])) # In order to concatenate shape[label,1]
    Sort=Counter(label.flatten()).most_common() 
    label_max=Sort[0][0]
    # Extraxt depth data from point cloud
    xcoord=[] 
    for x in range(len(imgre_wo_nan)):
        xcoord.append(imgre_wo_nan[x][0])
    xcoord=np.transpose(np.array([xcoord])) # shape[xcoord,1] 
    a=np.concatenate((label,xcoord),axis=1) # Put label and xcoord (depth) side by side shape[pixel,2]
    b=[] # Depth values from a which is at label_max
    for i in range(len(a)):
        if a[i,0]==label_max:
            b.append(a[i,1])
    avg_depth=np.mean(b)
    return avg_depth

def DBSCAN_pointcloud_old(img, eps=0.5):
    """
    img is point cloud image with three channels corresponding to x, y and z coordinate for each pixel.
    It must have the shape of [w,h,3]
    Coordinate system according to ZED2
    """
    imgre=img.reshape((-1,3)) # Flatten the image (pixel,3)
    imgre_wo_nan = imgre[~np.isnan(imgre).any(axis=1)] # remove rows with nan
    #imgre_wo_nan_and_inf = imgre_wo_nan[~np.isinf(imgre_wo_nan).any(axis=1)] # remove rows with inf
    imgre_scale = StandardScaler().fit_transform(imgre_wo_nan)

    DB_scale = DBSCAN(eps=eps).fit(imgre_scale)
    # Calculation of average depth
    label=DB_scale.labels_
    label=np.transpose(np.asarray([label])) # In order to concatenate shape[label,1]
    Sort=Counter(label.flatten()).most_common() 
    #print(Sort)
    
    label_max=Sort[0][0]
    #print(label.shape)
    
    # Extraxt depth data from point cloud
    xcoord=[] 
    for x in range(len(imgre_wo_nan)):
        xcoord.append(imgre_wo_nan[x][0])
    xcoord=np.transpose(np.array([xcoord])) # shape[xcoord,1] 
    #print(xcoord.shape)
    
    a=np.concatenate((label,xcoord),axis=1) # Put label and xcoord (depth) side by side shape[pixel,2]
    #print(a.shape)
    
    b=[] # Depth values from a which is at label_max
    for i in range(len(a)):
        if a[i,0]==label_max:
            b.append(a[i,1])
    avg_depth=np.mean(b)
    
    #avg_depth=1
    return avg_depth

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
