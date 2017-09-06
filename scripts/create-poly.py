import arcpy
from math import sqrt, sin, cos, radians, atan2, degrees
import pandas as pd



def angle_to(p1, p2, rotation=0, clockwise=False):
    angle = degrees(atan2(p2[1] - p1[1], p2[0] - p1[0])) - rotation
    if not clockwise:
        angle = -angle
    return angle % 360

def return_dir_angles(dir_ang):
    # using bearing to next frame, calculate bearing from centre point to each corner-point
    dir_ang_list = []
    angle = dir_ang + 45 # calculate first corner.  All other bearings will simply be +90deg on the previous value
    for i in range(4):
        angle += 90        
        dir_ang_list.append(angle % 360)
    return sorted({row for row in dir_ang_list})


def compute_points(dir_ang_list, h, x1, y1):
    # using trigonometry, calculate each corner point using the bearing and distance from the centre point.
    computed_points = []
    for angle in dir_ang_list:
        x = x1 + (h * cos(radians(angle)))
        y = y1 + (h * sin(radians(angle)))
        computed_points.append([x, y])
    return computed_points


# Get input parameters - points and target feature class
csv_in = arcpy.GetParameterAsText(0) # input csv of frame centre-points
fc = arcpy.GetParameterAsText(1) # fc output footprints will be written to
overwrite = arcpy.GetParameterAsText(2)


# delete any previous features in the output feature class if overwrite is true
if overwrite == 'true':
    arcpy.DeleteRows_management(fc)


# read csv into pandas dataframe
data_df = pd.read_csv(csv_in, keep_default_na=False)
# create new ID field.  This will form the unique field to select features on to process.  It is made up of Year, Month, Run, Run_Alpha
data_df["ID"] = data_df["ACQ_YEAR"].map(str)+'-'+data_df["ACQ_MONTH"]+'-'+data_df["RUN"].map(str)+'-'+data_df["RUN_ALPHA"]


# set-up cursor to insert new polygons into fc
fields = ['SHAPE@', 'CAPTURE', 'ACQ_MONTH', 'ACQ_YEAR', 'RUN', 'RUN_ALPHA', 'PHOTO', 'F_PLANE', 'F', 'HAGL', 'SCALE', 'MISSING']
cursor = arcpy.da.InsertCursor(fc, fields)


# set up counter and total to use in progress report to terminal
totalToProcess = len(data_df.ID.unique())
count = 0

# loop through each unique ID value from main dataframe
for i in data_df.ID.unique():
    # create new sub dataframe using unique ID    
    sub_df = data_df[data_df.ID == i]
    # sort the dataframe to ensure the frames are in correct order
    sub_df = sub_df.sort(['PHOTO'])
    # increaser counter and add progress message    
    count += 1
    arcpy.AddMessage("Processing {} of {} (Capture: {}, Run: {})".format(count, totalToProcess,sub_df.CAPTURE.unique()[0], sub_df.RUN.unique()[0]))
    # create list from frame values in dataframe
    frameList = sub_df['PHOTO'].tolist()
    
    # using the current frame and list of frames, calculate the next frame number, or previous frame number if current frame is the last one
    length = len(frameList)
    frameDict = {}
    for i in range(length):
        f1 =  frameList[i]
        if (i+1) == length:
            f2 = frameList[(i-1)]
        else:
            f2 = frameList[(i+1)]    
        # add to dict
        frameDict[f1] = f2

    # create two dictionaries to store frame number and matching x/y coordinate
    pointXDict = dict(zip(sub_df['PHOTO'], sub_df['POINT_X']))
    pointYDict = dict(zip(sub_df['PHOTO'], sub_df['POINT_Y']))


    # iterate over each row in sub dataframe
    for index, row in sub_df.iterrows():
        frame = row['PHOTO']
        # calculate the 'to frame', 'to x' and 'to y' using the previously created dictionaries
        toFrame = frameDict.get(frame)
        toX = pointXDict.get(toFrame)
        toY = pointYDict.get(toFrame)
        # create variables to store other values        
        capture = row['CAPTURE']			# year of capture, as in folder in which photos are contained.
        acq_month = row['ACQ_MONTH']		# Acquisition date of capture
        acq_year = row['ACQ_YEAR']		     # Acquisition month of capture
        run_no = row['RUN']				# run number
        run_alpha = row['RUN_ALPHA']		# alphas, i.e. 'N', 'S', 'W', 'W', 'A' etc. usually on tie runs.
        frame = row['PHOTO']				# frame number
        f_plane = row['F_PLANE']			# focal plane x (or y) distance in metres
        f_dist = row['F']					# focal distance in metres
        HAGL = row['HAGL']				# plane's altitude above sea level in metres
        x1 = row['POINT_X']
        y1 = row['POINT_Y']
        missing = row['MISSING']			# true if photo is missing form capture, false if not.
        if missing == 'TRUE':
            missing = 'We do not hold a copy of this photograph'
        else:
            missing = ''
       
        # add message to show frame progress        
#        arcpy.AddMessage("\tFrame: {0}".format(frame))  
        
        # calculate the x and y distances of the photo's extent on the ground
        ground_extent_xy = (HAGL/f_dist) * f_plane
        # calculate distance from centre-point to edge of frame
        dw = float(ground_extent_xy)/2
        dh = float(ground_extent_xy)/2
		
        # Calculate photoscale
        scale = HAGL/f_dist
		
        # calculate the distance to each frame corner-point from the centre point using pythagorean theorem        
        h = sqrt((dw*dw) + (dh*dh))
        
        # calculate bearing between current centre-point and next centre-point in run
        dir_ang = angle_to((x1, y1), (toX, toY), -90, True)
        # from centre-point and based on bearing to next centre-point, calculate bearings to each corner of footprint
        dir_ang_list = return_dir_angles(dir_ang)
        # calculate the x, y coordinates of each corner-point using the bearing, distance to edge of frame and centre-point x, y
        computed_points_list = compute_points(dir_ang_list, h, x1, y1)
        # Create polygon geometry from points     
        array = arcpy.Array([arcpy.Point(computed_points_list[0][0], computed_points_list[0][1]),
				arcpy.Point(computed_points_list[1][0], computed_points_list[1][1]),
				arcpy.Point(computed_points_list[2][0], computed_points_list[2][1]),
				arcpy.Point(computed_points_list[3][0], computed_points_list[3][1]),
				arcpy.Point(computed_points_list[0][0], computed_points_list[0][1])])
        poly = arcpy.Polygon(array)
        cursor.insertRow((poly, capture, acq_month, acq_year, run_no, run_alpha, frame, f_plane, f_dist, HAGL, scale, missing))

del cursor

arcpy.AddMessage('Processing Complete')
    