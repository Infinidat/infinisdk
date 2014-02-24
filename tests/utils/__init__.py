import flux
import infi.unittest
from infinipy2.izbox import IZBox
from infinipy2.infinibox import InfiniBox
from izsim import Simulator as IZBoxSimulator
from infinisim.infinibox import Infinibox as InfinisimInfinibox

flux.current_timeline.set_time_factor(0)

class InfiniboxSimulator(object):
    def __init__(self):
        self._simulator = InfinisimInfinibox()

        infinidat_user = self._simulator.users.get_by_name("infinidat")
        self._simulator.auth.push_user(infinidat_user)

    def start_context(self):
        self._simulator.activate()

    def end_context(self):
        self._simulator.deactivate()

    def get_address(self):
        return (self._simulator.get_floating_addresses()[0], 80)

simulators_dict = {IZBox: IZBoxSimulator, InfiniBox: InfiniboxSimulator}


class Infinipy2TestCase(infi.unittest.TestCase):
    SYSTEM_CLASS = None

    def setUp(self):
        super(Infinipy2TestCase, self).setUp()
        self.simulator = self._get_simulator()
        self.simulator.start_context()
        self.addCleanup(self.simulator.end_context)
        self.system = self.SYSTEM_CLASS(self.simulator.get_address())

    def interact(self):
        # For using this method, nose should be run with '-s' option
        from IPython import embed
        embed()

    def set_trace(self):
        from nose.tools import set_trace
        set_trace()

    def _get_simulator(self):
        return simulators_dict[self.SYSTEM_CLASS]()


class IZBoxTestCase(Infinipy2TestCase):
    SYSTEM_CLASS = IZBox

TestCase=IZBoxTestCase


class InfiniBoxTestCase(Infinipy2TestCase):
    SYSTEM_CLASS = InfiniBox

    def _create_volume(self, **kwargs):
        if not kwargs.get('pool_id') and not kwargs.get('pool'):
            kwargs['pool_id'] = self._create_pool().id
        vol = self.system.volumes.create(**kwargs)
        self.addCleanup(vol.delete)
        return vol

    def _create_pool(self, **kwargs):
        pool = self.system.pools.create(**kwargs)
        self.addCleanup(pool.delete)
        return pool


class CoreTestCase(Infinipy2TestCase):
    @infi.unittest.parameters.iterate('system_class', [IZBox, InfiniBox])
    def setUp(self, system_class):
        self.SYSTEM_CLASS = system_class
        super(CoreTestCase, self).setUp()
