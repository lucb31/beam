import scandir
import mapclassify

colors=['#0065BD', '#003359', '#98C6EA', '#7F7F7F', '#CCCCCC', '#A2AD00', '#E37222']
def get_working_dir(base_dir, iteration):
    return get_iteration_dir(get_run_dir(base_dir), iteration)


def get_run_dir(base_dir, latest_run=""):
    if latest_run == "":
        latest_run = get_latest_run()
    return base_dir + latest_run + "/"


def get_latest_run(base_dir):
    latest_run = '2020-01-01_00-00-00'
    for entry in scandir.scandir(base_dir):
        date = entry.name.split('2020')
        if len(date) > 1:
            if(date[1] > latest_run.split('2020')[1]):
                latest_run = entry.name
    return latest_run


def get_iteration_dir(run_dir, iteration):
    return run_dir + "ITERS/it." + str(iteration) + "/" + str(iteration) + "."


def get_last_iteration(run_dir):
    last_dir = ''
    for entry in scandir.scandir(run_dir + "ITERS/"):
        if entry.name > last_dir:
            last_dir = entry.name
    try:
        last_iteration = int(last_dir.split(".")[1])
    except:
        last_iteration = 0
    return last_iteration


def seconds_to_time_string(seconds):
    hour = int(seconds / 3600)
    minute = int((seconds - hour * 3600) / 60)
    string = ""
    if hour < 10:
        string += "0"
    string += str(hour) + ":"
    if minute < 10:
        string += "0"
    string += str(minute)
    return string


def range_inclusive(start, stop, step):
    inclusive_range = [val for val in range(start, stop, step)]
    inclusive_range.append(stop)
    return inclusive_range


def mask_munich_road_shape(path_to_munich_shape, path_to_munich_polygon, path_to_munich_road_masked):
    munich_enclosing_roads = gpd.read_file(path_to_munich_shape)
    munich_enclosing_roads.to_crs(crs=crs)
    munich_polygon = gpd.read_file(path_to_munich_polygon)
    munich_polygon.to_crs(crs=crs)
    mask = munich_enclosing_roads.within(munich_polygon.geometry[0])
    munich_enclosing_roads_masked = munich_enclosing_roads[mask]
    munich_enclosing_roads_masked[['osm_id', 'name', 'z_order', 'geometry']].to_file(path_to_munich_road_masked)


def scale_within_boundaries(minval, maxval):
    def scalar(val):
        new_scheme = mapclassify.UserDefined([val], bins=scheme.bins)
        bin = new_scheme.yb[0]
        return bin*2 + 5
    return scalar


def scale_by_scheme(val, scheme):
    new_scheme = mapclassify.UserDefined([val], bins=scheme.bins)
    bin = new_scheme.yb[0]
    return (bin*2 + 5)*6
