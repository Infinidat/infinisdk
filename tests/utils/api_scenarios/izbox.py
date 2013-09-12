from .utils import *

GET("/api/rest/system") >> OK(JSON({"error": null, "metadata": {"ready": true}, "result": {"name": "izbox-25001", "serial": 25001, "version": "0.2.post88.g4237415"}})) # AUTOUPDATE
