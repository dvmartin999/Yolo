from collections import Counter
import numpy as np
import cv2
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import sensor_msgs.point_cloud2 as pc2
from geometry_msgs.msg import PoseStamped


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

def PC_dataxyz_to_PC_image(data,Org_img_height=720,Org_img_width=1280):
    """
    Extract xyz coordinates from point cloud and transform them an image

    data: pointcloud from ZED2 
    Org_img_height: Height of image defined in ZED2
    Org_img_width: Wigth of image defined in ZED2
    """
    pc = pc2.read_points(data, skip_nans=False, field_names=("x", "y", "z"))
    pc_list = []
    for p in pc:
        pc_list.append([p[0],p[1],p[2]]) # Extract x,y and z coordinates from point cloud
    pc_list=np.array(pc_list, dtype='float32') # cv2.getRectSubPix need float32 (Sub_pointcloud function)
    PC_image=pc_list.reshape((Org_img_height,Org_img_width,3)) # Transform list into image
    return pc_list, PC_image

def Sub_pointcloud(PC_image, bboxes):   
    """
    Extract sub images with the size of bounding box from point cloud image

    PC_image: Point cloud image [h,w,3]
    bboxes: Bounding boxes from yolov3
    """
    PC_image_bbox_sub_series = []
    x1, y1, x2, y2, _, _ = Give_boundingbox_coor_class(bboxes)
    for i in range(len(bboxes)):
        patch=(int(x2[i]-x1[i]),int(y2[i]-y1[i])) # gives width and height of bbox
        center=(int(x1[i]+patch[0]/2),int(y1[i]+patch[1]/2)) # gives center coodintes of bbox global
        PC_image_bbox_sub = cv2.getRectSubPix(PC_image,patch,center) # Extract bbox in depth image
        PC_image_bbox_sub_series.append(PC_image_bbox_sub)

    return PC_image_bbox_sub_series

def NormalizeData(data):
    return (data - np.nanmin(data)) / (np.nanmax(data) - np.nanmin(data))

def DBSCAN_pointcloud(img, bboxes, seg_plot=True, eps=0.046, procent=0.0011):
    avg_depth_series = []
    segmented_img_color_series = []
    xyzcoord_series =[]
    for i in range(len(bboxes)):
        imgre=img[i].reshape((-1,3)) # Flatten the image (pixel,3)
        min_samples=int(len(imgre)*procent)
        imgre_wo_nan = imgre[~np.isnan(imgre).any(axis=1)] # remove rows with nan
        imgre_wo_nan_inf = imgre_wo_nan[~np.isinf(imgre_wo_nan).any(axis=1)] # remove rows with inf
        # Perform kmeans with xyz data
        imgre_scale = StandardScaler().fit_transform(imgre_wo_nan_inf)
        DBSCAN_scale = DBSCAN(eps=eps, min_samples=min_samples).fit(imgre_scale)
        # Calculation of average depth
        label=DBSCAN_scale.labels_
        label_for_plot=np.array(label) #[label,]
        label=np.transpose(np.asarray([label])) # In order to concatenate shape[label,1]
        Sort=Counter(label.flatten()).most_common() 
        label_max=Sort[0][0]

        xcoord=[]
        ycoord=[]
        zcoord=[]
        for xyz in range(len(imgre_wo_nan_inf)):
            xcoord.append(imgre_wo_nan_inf[xyz][0])
            ycoord.append(imgre_wo_nan_inf[xyz][1])
            zcoord.append(imgre_wo_nan_inf[xyz][2])
        xcoord=np.transpose(np.array([xcoord])) # shape[xcoord,1] 
        ycoord=np.transpose(np.array([ycoord])) # shape[ycoord,1] 
        zcoord=np.transpose(np.array([zcoord])) # shape[zcoord,1]

        a=np.concatenate((label,xcoord),axis=1) # Put label and xcoord (depth) side by side shape[pixel,2]
        b=[] # Depth values from a which is at label_max
        for len_a in range(len(a)):
            if a[len_a,0]==label_max:
                b.append(a[len_a,1])
        
        min_x=np.min(b) # find minimum depth in object
        min_index=np.where(xcoord[:,0]==min_x) # Find index of min x in xcoord
        y_for_min_x = ycoord[min_index[0][0],0] # get y from min_index
        z_for_min_x = zcoord[min_index[0][0],0] # get z from min_index
            
        xyzcoord=[min_x,y_for_min_x,z_for_min_x]
        xyzcoord_series.append(xyzcoord)
        
        avg_depth=np.mean(b)
        avg_depth_series.append(avg_depth)
        
        if seg_plot==True:
            depth_distance=[] 
            for depth_coord in range(len(imgre)):
                depth_distance.append(imgre[depth_coord][0])
            depth_distance=np.array(depth_distance)
            
            labels = np.array(np.empty(len(depth_distance))) # Initialize labels array with the length of nr pixels in img
            labels[:] = np.nan # All index are nan
            labels[np.invert(np.isnan(depth_distance))]=label_for_plot
            labels = np.where(np.isnan(labels), 1000 ,labels) #
            labels = np.where(np.isinf(labels), 1000 ,labels) # 
            for clust in range(-1,len(Sort)-1,1):
                if clust != label_max:
                    labels = np.where(labels==clust,2000,labels)
            
            labels_img=np.array(labels.reshape(img[i].shape[0],img[i].shape[1],1)) # Convert labels into img one channel
            labels_img_3c=cv2.merge((labels_img,labels_img,labels_img)) # Convert label_img into three channels

            #Change labels_img_3c so ch 2 is max clust, ch3 is rest for segmented image
            seg1=np.where((labels_img_3c[:,:,0]==label_max))
            seg3=np.where((labels_img_3c[:,:,0]==2000))
            segnaninf=np.where((labels_img_3c[:,:,0]==1000))

            segmented_img=labels_img_3c
            segmented_img[seg1]=(0,1,0)
            segmented_img[seg3]=(0,0,1)
            segmented_img[segnaninf]=(0,0,0)
            
            # Create segmented image
            segmented_img_color=segmented_img*255 # Tranfer into RGB
            segmented_img_color[segnaninf]=(255,255,255) #Makes nan and inf white
            segmented_img_color=segmented_img_color.astype("uint8") # Change type
            segmented_img_color_series.append(segmented_img_color)

    return avg_depth_series, segmented_img_color_series, xyzcoord_series

def k_means_pointcloud(img, bboxes, PC=True, seg_plot=True, k=3,max_iter=1000,tol=1e-4):
    """
    Performs kmeans on point cloud in order to segment object

    INPUT:
    seg_plot=True output segmentation image (works only for k=3)
    seg_plot=False does not output segmentation image 
    PC=True use xyz from point cloud
    PC=False use x from point cloud (depth image)
    img = PC_image_bbox_sub_series
    img is a point cloud image with three channels corresponding to x, y and z coordinate for each pixel.
    It must have the shape of [h,w,3]
    Coordinate system according to ZED2

    OUTPUT:

    """
    if PC==True:
        avg_depth_series = []
        segmented_img_color_series = []
        xyzcoord_series =[]
        for i in range(len(bboxes)):
            imgre=img[i].reshape((-1,3)) # Flatten the image (pixel,3)
            imgre_wo_nan = imgre[~np.isnan(imgre).any(axis=1)] # remove rows with nan
            imgre_wo_nan_inf = imgre_wo_nan[~np.isinf(imgre_wo_nan).any(axis=1)] # remove rows with inf
            # Perform kmeans with xyz data
            imgre_scale = StandardScaler().fit_transform(imgre_wo_nan_inf)
            KM_scale = KMeans(n_clusters=k, max_iter=max_iter, tol=tol, random_state=0).fit(imgre_scale)
            # Calculation of average depth
            label=KM_scale.labels_
            label_for_plot=np.array(label) #[label,]
            label=np.transpose(np.asarray([label])) # In order to concatenate shape[label,1]
            Sort=Counter(label.flatten()).most_common() 
            label_max=Sort[0][0]
            # Extraxt depth data from point cloud
            xcoord=[] #depth
            ycoord=[]
            zcoord=[]
            for xyz in range(len(imgre_wo_nan_inf)):
                xcoord.append(imgre_wo_nan_inf[xyz][0])
                ycoord.append(imgre_wo_nan_inf[xyz][1])
                zcoord.append(imgre_wo_nan_inf[xyz][2])
            xcoord=np.transpose(np.array([xcoord])) # shape[xcoord,1] 
            ycoord=np.transpose(np.array([ycoord])) # shape[ycoord,1] 
            zcoord=np.transpose(np.array([zcoord])) # shape[zcoord,1]

            a=np.concatenate((label,xcoord),axis=1) # Put label and xcoord (depth) side by side shape[pixel,2]
            b=[] # Depth values from a which is at label_max
            for len_a in range(len(a)):
                if a[len_a,0]==label_max:
                    b.append(a[len_a,1])
            
            min_x=np.min(b) # find minimum depth
            min_index=np.where(xcoord[:,0]==min_x) # Find index of min x in xcoord
            y_for_min_x = ycoord[min_index[0][0],0] # get y from min_index
            z_for_min_x = zcoord[min_index[0][0],0] # get z from min_index
            
            xyzcoord=[min_x,y_for_min_x,z_for_min_x]
            xyzcoord_series.append(xyzcoord)

            avg_depth=np.mean(b)
            avg_depth_series.append(avg_depth)
            
            #%% For plotting segmented image (work only for k=3)
            if seg_plot==True:
                depth_distance=[] 
                for depth_coord in range(len(imgre)):
                    depth_distance.append(imgre[depth_coord][0])
                depth_distance=np.array(depth_distance)

                labels = np.array(np.empty(len(depth_distance))) # Initialize labels array with the length of nr pixels in img
                labels[:] = np.nan # All index are nan
                labels[np.invert(np.isnan(depth_distance))]=label_for_plot
                labels = np.where(np.isnan(labels), k ,labels) # set nan to category 3
                labels = np.where(np.isinf(labels), k ,labels) # set +- inf to category 3
                labels_img=np.array(labels.reshape(img[i].shape[0],img[i].shape[1],1)) # Convert labels into img one channel
                labels_img_3c=cv2.merge((labels_img,labels_img,labels_img)) # Convert label_img into three channels

                #Change labels_img_3c so ch 1 is seg1, ch2 is seg2 and ch3 is seg3 for segmented image
                seg1=np.where((labels_img_3c[:,:,0]==0))# & (labels_img_3c[:,:,1]==0) & (labels_img_3c[:,:,2]==0))
                seg2=np.where((labels_img_3c[:,:,0]==1))# & (labels_img_3c[:,:,1]==1) & (labels_img_3c[:,:,2]==1))
                seg3=np.where((labels_img_3c[:,:,0]==2))# & (labels_img_3c[:,:,1]==2) & (labels_img_3c[:,:,2]==2))
                segnaninf=np.where((labels_img_3c[:,:,0]==3))# & (labels_img_3c[:,:,1]==3) & (labels_img_3c[:,:,2]==3))

                segmented_img=labels_img_3c
                segmented_img[seg1]=(1,0,0)
                segmented_img[seg2]=(0,1,0)
                segmented_img[seg3]=(0,0,1)
                segmented_img[segnaninf]=(0,0,0)
            
                # Create segmented image with depth data 
                #depth_distance_img=np.array(depth_distance.reshape(img[i].shape[0],img[i].shape[1],1))

                #segmented_img_3c=segmented_img*depth_distance_img
                #segmented_img_3c_norm=NormalizeData(segmented_img_3c) # Normalize segmented image
                segmented_img_color=segmented_img*255 # Tranfer into RGB
                segmented_img_color[segnaninf]=(255,255,255) #Makes nan and inf white
                segmented_img_color=segmented_img_color.astype("uint8")
                segmented_img_color_series.append(segmented_img_color)
    
    elif PC==False:
        avg_depth_series = []
        segmented_img_color_series = []
        xyzcoord_series =[]
        for i in range(len(bboxes)):
            imgre=img[i].reshape((-1,3)) # Flatten the image (pixel,3)
            imgre_wo_nan = imgre[~np.isnan(imgre).any(axis=1)] # remove rows with nan
            imgre_wo_nan_inf = imgre_wo_nan[~np.isinf(imgre_wo_nan).any(axis=1)] # remove rows with inf
            # Extraxt depth data from point cloud
            xcoord=[] 
            for x in range(len(imgre_wo_nan_inf)):
                xcoord.append(imgre_wo_nan_inf[x][0])
            xcoord=np.transpose(np.array([xcoord])) # shape[xcoord,1]
            # Perform kmeans with x data 
            imgre_scale = StandardScaler().fit_transform(xcoord)
            KM_scale = KMeans(n_clusters=k, max_iter=max_iter, tol=tol, random_state=0).fit(imgre_scale)
            # Calculation of average depth
            label=KM_scale.labels_
            label_for_plot=np.array(label) #[label,]
            label=np.transpose(np.asarray([label])) # In order to concatenate shape[label,1]
            Sort=Counter(label.flatten()).most_common() 
            label_max=Sort[0][0]

            a=np.concatenate((label,xcoord),axis=1) # Put label and xcoord (depth) side by side shape[pixel,2]
            b=[] # Depth values from a which is at label_max
            for len_a in range(len(a)):
                if a[len_a,0]==label_max:
                    b.append(a[len_a,1])
            avg_depth=np.mean(b)
            avg_depth_series.append(avg_depth)

            #%% For plotting segmented image (work only for k=3)
            if seg_plot==True:
                depth_distance=[] 
                for depth_coord in range(len(imgre)):
                    depth_distance.append(imgre[depth_coord][0])
                depth_distance=np.array(depth_distance)

                labels = np.array(np.empty(len(depth_distance))) # Initialize labels array with the length of nr pixels in img
                labels[:] = np.nan # All index are nan
                labels[np.invert(np.isnan(depth_distance))]=label_for_plot
                labels = np.where(np.isnan(labels), k ,labels) # set nan to category 3
                labels = np.where(np.isinf(labels), k ,labels) # set +- inf to category 3
                labels_img=np.array(labels.reshape(img[i].shape[0],img[i].shape[1],1)) # Convert labels into img one channel
                labels_img_3c=cv2.merge((labels_img,labels_img,labels_img)) # Convert label_img into three channels

                #Change labels_img_3c so ch 1 is seg1, ch2 is seg2 and ch3 is seg3 for segmented image
                seg1=np.where((labels_img_3c[:,:,0]==0))# & (labels_img_3c[:,:,1]==0) & (labels_img_3c[:,:,2]==0))
                seg2=np.where((labels_img_3c[:,:,0]==1))# & (labels_img_3c[:,:,1]==1) & (labels_img_3c[:,:,2]==1))
                seg3=np.where((labels_img_3c[:,:,0]==2))# & (labels_img_3c[:,:,1]==2) & (labels_img_3c[:,:,2]==2))
                segnaninf=np.where((labels_img_3c[:,:,0]==3))# & (labels_img_3c[:,:,1]==3) & (labels_img_3c[:,:,2]==3))

                segmented_img=labels_img_3c
                segmented_img[seg1]=(1,0,0)
                segmented_img[seg2]=(0,1,0)
                segmented_img[seg3]=(0,0,1)
                segmented_img[segnaninf]=(0,0,0)
            
                # Create segmented image with depth data 
                depth_distance_img=np.array(depth_distance.reshape(img[i].shape[0],img[i].shape[1],1))

                segmented_img_3c=segmented_img*depth_distance_img
                segmented_img_3c_norm=NormalizeData(segmented_img_3c) # Normalize segmented image
                segmented_img_color=segmented_img_3c_norm*255 # Tranfer into RGB
                segmented_img_color[segnaninf]=(255,255,255) #Makes nan and ing white
                segmented_img_color=segmented_img_color.astype("uint8")
                segmented_img_color_series.append(segmented_img_color)
    
    else:
        print("PC must be True or False")
        avg_depth_series=np.nan
        segmented_img_color_series = []
        xyzcoord_series = np.nan

    return avg_depth_series, segmented_img_color_series, xyzcoord_series

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

def PC_reduc(Target, TargetOrder, pc_list, cloud):
    Start_x = Target[TargetOrder("Start_x")]
    Start_y = Target[TargetOrder("Start_y")]
    End_x   = Target[TargetOrder("End_x")]
    End_y   = Target[TargetOrder("End_y")]

    bbox_i = []
    for y in range(Start_y,End_y):
        bbox_i += list(range((y*672+Start_x)*3,(y*672+End_x+1)*3))
    pc_list = np.delete(pc_list, bbox_i)
    pc_list = pc_list.reshape(int(len(pc_list)/3),3)
    pc_list= pc_list[~np.isnan(pc_list).any(axis=1)]
    pc_list= pc_list[~np.isinf(pc_list).any(axis=1)]
    header = cloud.header
    Reduced_PC2 = pc2.create_cloud_xyz32(header, pc_list)
    return Reduced_PC2

def Waypoint_planter(Target, TargetOrder, Frame_id, Time):
    Pose = PoseStamped()
    Pose.header.stamp = Time
    Pose.header.frame_id = Frame_id #"zed2_left_camera_frame"
    Pose.pose.position.x = Target[TargetOrder("Depth_X")]
    Pose.pose.position.y = Target[TargetOrder("Depth_Y")]
    Pose.pose.position.z = Target[TargetOrder("Depth_Z")]
    Pose.pose.orientation.x = float(0)
    Pose.pose.orientation.y = float(0)
    Pose.pose.orientation.z = float(0)
    Pose.pose.orientation.w = float(1)
    return Pose
    