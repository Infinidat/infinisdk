class InfiniboxCluster(object):
    """Manages higher-level operations relating to the clustered nature of the system
    """

    def __init__(self, system):
        super(InfiniboxCluster, self).__init__()
        self.system = system
