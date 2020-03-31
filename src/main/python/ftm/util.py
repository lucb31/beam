import scandir


def get_working_dir(base_dir, iteration):
    return get_iteration_dir(get_run_dir(base_dir), iteration)


def get_run_dir(base_dir, latest_run=""):
    if latest_run == "":
        latest_run = get_latest_run()
    return base_dir + latest_run + "/"


def get_latest_run(base_dir):
    latest_run = ''
    for entry in scandir.scandir(base_dir):
        if entry.name > latest_run:
            latest_run = entry.name
    return latest_run


def get_iteration_dir(run_dir, iteration):
    return run_dir + "ITERS/it." + str(iteration) + "/" + str(iteration) + "."


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