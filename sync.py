
import subprocess
import pandas as pd
import config


def sync(survey):
    local_path = f'{config.path}/data/{survey}.csv'
    remote_path = f'{config.remote}/{survey}.csv'

    # check if remote file exists; if not, copy up and return
    try:
        subprocess.run(
                f'rclone lsf {remote_path}',
                shell=True,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as e:
        # return code 3 means not found
        if e.returncode == 3:
            subprocess.run(
                    f'rclone copy {local_path} {config.remote}',
                    shell=True,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
            )
            return
        else:
            raise
            

    # download remote data, load remote data and local data
    subprocess.run(
            f'rclone copy {remote_path} {config.path}/data/tmp',
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
    )
    remote_data = pd.read_csv(
            f'{config.path}/data/tmp/{survey}.csv',
            na_values=[],
            keep_default_na=False
    )
    local_data = pd.read_csv(
            local_path,
            na_values=[],
            keep_default_na=False
    )
    
    # combine dataframes by concatenating and dropping duplicates
    data = pd.concat((local_data, remote_data))
    data = data.drop_duplicates()
    # rough check that no local data was destroyed
    assert len(data)>=len(local_data), 'sync aborted: too many rows dropped'
    # sort by date and time for cleanliness
    data = data.sort_values(by=['date','time'], na_position='first')

    # write data to local, copy to remote
    data.to_csv(local_path, index=False)
    subprocess.run(
            f'rclone copy {local_path} {config.remote}',
            shell=True,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
    )
