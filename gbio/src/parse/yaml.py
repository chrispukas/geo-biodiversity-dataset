import yaml
import os


def load_yaml(path: str):
    assert os.path.exists(path)
    assert path.endswith(".yml")

    with open(path) as stream:
        try:
           return yaml.safe_load(stream=stream)
        except yaml.YAMLError as err:
            print(err)
