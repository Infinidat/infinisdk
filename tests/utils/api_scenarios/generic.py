from .utils import *

generic_scenario = Rules(
    GET("/api/rest/system") >> OK(JSON({"hello": "there"})),
)



