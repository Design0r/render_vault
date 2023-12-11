import os
from typing import Protocol

import requests

from .logger import Logger


class APIHandler(Protocol):
    @staticmethod
    def create(name: str, path: str) -> int:
        ...

    @staticmethod
    def delete(name: str, path: str) -> int:
        ...


class MaterialAPIHandler:
    @staticmethod
    def create(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/materials/create"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code

    @staticmethod
    def delete(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/materials/delete"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code


class ModelAPIHandler:
    @staticmethod
    def create(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/models/create"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code

    @staticmethod
    def delete(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/models/delete"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code


class HDRIAPIHandler:
    @staticmethod
    def create(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/hdris/create"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code

    @staticmethod
    def delete(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/hdris/delete"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code


class LightsetAPIHandler:
    @staticmethod
    def create(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/lightsets/create"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code

    @staticmethod
    def delete(name: str, path: str) -> int:
        SERVER = os.getenv("SERVER_ADDRESS")
        url = f"http://{SERVER}/lightsets/delete"
        body = {"name": name, "path": path}
        response = requests.post(url, json=body)

        Logger.debug(response)
        return response.status_code


def get_all_pools() -> tuple[dict, dict, dict, dict]:
    SERVER = os.getenv("SERVER_ADDRESS")
    url = f"http://{SERVER}/all_pools"
    response = requests.get(url).json()
    materials = {
        pool.get("name"): pool.get("path") for pool in response.get("materials")
    }

    models = {pool.get("name"): pool.get("path") for pool in response.get("models")}
    hdris = {pool.get("name"): pool.get("path") for pool in response.get("hdris")}
    lightsets = {
        pool.get("name"): pool.get("path") for pool in response.get("lightsets")
    }
    return (
        dict(sorted(materials.items())),
        dict(sorted(models.items())),
        dict(sorted(hdris.items())),
        dict(sorted(lightsets.items())),
    )
