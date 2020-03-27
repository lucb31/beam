import scandir

def get_working_dir(base_dir, iteration):
    return get_iteration_dir(get_run_dir(base_dir), iteration)

def get_run_dir(base_dir):
    return base_dir + get_latest_run(base_dir) + "/"

def get_latest_run(base_dir):
    latest_run = ''
    for entry in scandir.scandir(base_dir):
        if entry.name > latest_run:
            latest_run = entry.name
    return latest_run

def get_iteration_dir(run_dir, iteration):
    return run_dir + "ITERS/it." + str(iteration) + "/" + str(iteration) + "."