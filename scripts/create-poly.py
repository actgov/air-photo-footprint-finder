import arcpy
from math import sqrt
from math import tan, sin, cos, radians, pi, atan2, degrees
import csv


def angle_to(p1, p2, rotation=0, clockwise=False):
    angle = degrees(atan2(p2[1] - p1[1], p2[0] - p1[0])) - rotation
    if not clockwise:
        angle = -angle
    return angle % 360

def return_dir_angles(dir_ang):
    if dir_ang < 90 and dir_ang >= 0:
        if dir_ang < 45 and dir_ang >= 0:
            p1_dir_ang = dir_ang + 45
            p2_dir_ang = p1_dir_ang + 90
            p3_dir_ang = p1_dir_ang + 180
            p4_dir_ang = p1_dir_ang + 270
        else:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang  + 90
            p3_dir_ang = p1_dir_ang  + 180
            p4_dir_ang = p1_dir_ang  + 270
    elif dir_ang < 180 and dir_ang >= 90:
        if dir_ang < 135 and dir_ang >= 90:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang + 90
            p3_dir_ang = p1_dir_ang + 180
            p4_dir_ang = p1_dir_ang + 270
        else:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang  + 90
            p3_dir_ang = p1_dir_ang  + 180
            p4_dir_ang = p1_dir_ang  - 90
    elif dir_ang < 270 and dir_ang >= 180:
        if dir_ang < 225 and dir_ang >= 180:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang + 90
            p3_dir_ang = p1_dir_ang + 180
            p4_dir_ang = p1_dir_ang - 90
        else:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang  + 90
            p3_dir_ang = p1_dir_ang  - 180
            p4_dir_ang = p1_dir_ang  - 90
    elif dir_ang < 360 and dir_ang >= 270:
        if dir_ang < 315 and dir_ang >= 270:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang + 90
            p3_dir_ang = p1_dir_ang - 180
            p4_dir_ang = p1_dir_ang - 90
        else:
            p1_dir_ang = dir_ang - 45
            p2_dir_ang = p1_dir_ang  - 270
            p3_dir_ang = p1_dir_ang  - 180
            p4_dir_ang = p1_dir_ang  - 90
    return [p1_dir_ang, p2_dir_ang, p3_dir_ang, p4_dir_ang]


def compute_points(dir_ang_list, h, x1, y1):
    computed_points = []
    for dir_ang in dir_ang_list:
        if dir_ang < 90 and dir_ang >= 0:
            x2 = x1 + (h*cos(radians(dir_ang-0)))
            y2 = y1 + (h*sin(radians(dir_ang-0)))
            computed_points.append([x2, y2])
        elif dir_ang < 180 and dir_ang >= 90:
            x2 = x1 + (h*sin(radians(dir_ang-90)))
            y2 = y1 - (h*cos(radians(dir_ang-90)))
            computed_points.append([x2, y2])
        elif dir_ang < 270 and dir_ang >= 180:
            x2 = x1 - (h*cos(radians(dir_ang-180)))
            y2 = y1 - (h*sin(radians(dir_ang-180)))
            computed_points.append([x2, y2])
        else:
            x2 = x1 - (h*sin(radians(dir_ang-270)))
            y2 = y1 + (h*cos(radians(dir_ang-270)))
            computed_points.append([x2, y2])
    return computed_points
    
# Get input parameters - points and target feature class
pts = arcpy.GetParameter(0)
fc = arcpy.GetParameterAsText(1)
csv_in = arcpy.GetParameterAsText(2)

f = open(csv_in, 'rb')
reader = csv.reader(f)
photo_list = list(reader)[1:]



run_ids = []
for photo in photo_list:
    if [photo[3], photo[4]] not in run_ids:
        run_ids.append([photo[3], photo[4]])
runs = []
for run_id in run_ids:
    photos_in_run = []
    run_number = run_id[0]
    run_alpha = run_id[1]
    for photo in photo_list:
        photo_run_number = photo[3]
        photo_run_alpha = photo[4]
        if (run_number == photo_run_number) and (run_alpha == photo_run_alpha):
            photo_dict = {}
            photo_dict['CAPTURE']    = int(photo[0])
            photo_dict['ACQ_MONTH']  = photo[1]
            photo_dict['ACQ_YEAR']   = int(photo[2])
            photo_dict['RUN']        = int(photo[3])
            photo_dict['RUN_ALPHA']  = photo[4]
            photo_dict['PHOTO']      = int(photo[5])
            photo_dict['POINT_X']    = float(photo[6])
            photo_dict['POINT_Y']    = float(photo[7])
            photo_dict['MISSING']    = photo[8]
            photo_dict['F_PLANE']    = float(photo[9])
            photo_dict['F']          = float(photo[10])
            photo_dict['HAGL']       = int(photo[11])
            photos_in_run.append(photo_dict)
    runs.append(photos_in_run)

# create new polygons from points

fields = ['SHAPE@', 'CAPTURE', 'ACQ_MONTH', 'ACQ_YEAR', 'RUN', 'RUN_ALPHA', 'PHOTO', 'F_PLANE', 'F', 'HAGL', 'SCALE', 'MISSING']
cursor = arcpy.da.InsertCursor(fc, fields)
for run in runs:
    final_frame = 0
    for photo in run:
        if int(photo['PHOTO']) > final_frame:
            final_frame = int(photo['PHOTO'])
    for photo in run:
        capture = photo['CAPTURE']			# year of capture, as in folder in which photos are contained.
        acq_month = photo['ACQ_MONTH']		# Acquisition date of capture
        acq_year = photo['ACQ_YEAR']		# Acquisition month of capture
        run_no = photo['RUN']				# run number
        run_alpha = photo['RUN_ALPHA']		# alphas, i.e. 'N', 'S', 'W', 'W', 'A' etc. usually on tie runs.
        frame = photo['PHOTO']				# frame number
        f_plane = photo['F_PLANE']			# focal plane x (or y) distance in metres
        f_dist = photo['F']					# focal distance in metres
        HAGL = photo['HAGL']				# plane's altitude above sea level in metres
        x1 = photo['POINT_X']
        y1 = photo['POINT_Y']
        missing = photo['MISSING']			# true if photo is missing form capture, false if not.
        if missing == 'TRUE':
            missing = 'We do not hold a copy of this photograph'
        else:
            missing = ''
        
		# calculate the x and y distances of the photo's extent on the ground
        ground_extent_xy = (HAGL/f_dist) * f_plane
		
        dw = float(ground_extent_xy)/2
        dh = float(ground_extent_xy)/2
		
		# Calculate photoscale
        scale = f_dist/HAGL
		
        h = sqrt((dw*dw) + (dh*dh))
        try:
            x2 = run[run.index(photo)+1]['POINT_X']
            y2 = run[run.index(photo)+1]['POINT_Y']
        except IndexError:
            x2 = x1
            y2 = y1
            x1 = run[run.index(photo)-1]['POINT_X']
            y1 = run[run.index(photo)-1]['POINT_Y']
        dir_ang = angle_to((x1, y1), (x2, y2), -90, True)
        dir_ang_list = return_dir_angles(dir_ang)
        computed_points_list = compute_points(dir_ang_list, h, x1, y1)
        print(computed_points_list)
		# Create polygon geometry from points     
        array = arcpy.Array([arcpy.Point(computed_points_list[0][0], computed_points_list[0][1]),
				arcpy.Point(computed_points_list[1][0], computed_points_list[1][1]),
				arcpy.Point(computed_points_list[2][0], computed_points_list[2][1]),
				arcpy.Point(computed_points_list[3][0], computed_points_list[3][1]),
				arcpy.Point(computed_points_list[0][0], computed_points_list[0][1])])
        poly = arcpy.Polygon(array)
        cursor.insertRow((poly, capture, acq_month, acq_year, run_no, run_alpha, frame, f_plane, f_dist, HAGL, scale, missing))
del cursor
