import pytest
import os
import threading
import time
import multiprocessing
import subprocess
from helpers.nodes_logs_parser import IntegrationTest, TOTAL_NODES, LogEntry

class RunFor10Minutes(IntegrationTest):
    TEN_MINUTES_SECS = 600

    def __init__(self,timeout_event,shared_success_value):
        super().__init__(max_running_time_secs=620)
        self.node_state = dict()
        self.could_sync = False
        self.timeout_event = timeout_event
        self.shared_success_value = shared_success_value


    def custom_process_log_entry(self, log_entry: LogEntry):
        if log_entry.node_id is not None:
            self.node_state[log_entry.node_id] = log_entry.sync_state
            if len(self.node_state) == TOTAL_NODES and not self.could_sync:
                if all(s == 'synced' for s in self.node_state.values()):
                    IntegrationTest.writeout("******************** NODES SYNCED ********************")
                    self.could_sync = True

        if time.time() - self.start_time > self.TEN_MINUTES_SECS:
         if self.could_sync:
            self.shared_success_value.value = 1
         else:
            self.shared_success_value.value = 0
         self.timeout_event.set()


@pytest.fixture(scope="function")
def setup(request):
    yield
    current_path = os.path.dirname(__file__)
    script_path = os.path.join(current_path,'..','helpers/reset_net.sh')
    subprocess.call([script_path])

@pytest.mark.runfor10minutes
def test_nodes_synced(setup):
    success_value = multiprocessing.Value('i',0)
    timeout_event =  multiprocessing.Event()
    test = RunFor10Minutes(timeout_event,success_value)
    w1 = multiprocessing.Process(
        name='nodes',
        target=test.start,
        args=(),
    )
    w1.start()
    timeout_event.wait()
    if success_value.value != 1:
       w1.terminate()
       assert False
