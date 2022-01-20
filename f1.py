from flask import Flask, request, abort, make_response
from prometheus_client import MetricsHandler, generate_latest, CONTENT_TYPE_LATEST
from prometheus_client.core import CollectorRegistry, REGISTRY, Counter, Gauge, GaugeMetricFamily, CounterMetricFamily
import os
import psutil
import socket


app = Flask(__name__)



class CpuTimeCollector(object):
    """
    CPU time may be translated in percent later
    """
    cpu_time_collector_run_time = Gauge('solaris_exporter_cpu_time_processing', 'Time spent processing request')

    def collect(self):
        with self.cpu_time_collector_run_time.time():
            worker_stat_cpu_time = CounterMetricFamily('solaris_exporter_cpu_time',
                                                       'python psutil counters, CPU usage time.',
                                                       labels=['host', 'statistic'])
            cpuinfo = psutil.cpu_times(percpu=False)
            worker_stat_cpu_time.add_metric([host_name, 'user'], cpuinfo.user)
            worker_stat_cpu_time.add_metric([host_name, 'system'], cpuinfo.system)
            worker_stat_cpu_time.add_metric([host_name, 'idle'], cpuinfo.idle)
            worker_stat_cpu_time.add_metric([host_name, 'nice'], cpuinfo.nice)
        yield worker_stat_cpu_time


class CpuLoadCollector(object):
    """
    CPU load average 1, 5, 15 min, cpu count
    """
    cpu_load_collector_run_time = Gauge('solaris_exporter_cpu_load_processing', 'Time spent processing request')

    def collect(self):
        with self.cpu_load_collector_run_time.time():
            worker_stat_cpu_load = GaugeMetricFamily('solaris_exporter_cpu_load',
                                                     'python psutil counters, system load avg.',
                                                     labels=['host', 'statistic'])
            cpuinfo = os.getloadavg()
            worker_stat_cpu_load.add_metric([host_name, 'load1m'], cpuinfo[0])
            worker_stat_cpu_load.add_metric([host_name, 'load5m  '], cpuinfo[1])
            worker_stat_cpu_load.add_metric([host_name, 'load15m'], cpuinfo[2])
            cpuinfo = len(psutil.cpu_percent(interval=None, percpu=True))
            worker_stat_cpu_load.add_metric([host_name, 'vcpu'], cpuinfo)
        yield worker_stat_cpu_load

@app.route('/metrics', methods=['GET'])
def get_metrics():
      if request.remote_addr != '10.20.30.40':
        abort(403)

      collectors = [
        CpuTimeCollector(),
        CpuLoadCollector(),
      ]

      REGISTRY = CollectorRegistry()
      for c in collectors:
          REGISTRY.register(c)

      resp = make_response(generate_latest(REGISTRY), 200)
      resp.headers['Content-type'] = CONTENT_TYPE_LATEST
      return resp


if __name__ == "__main__":
    host_name = socket.gethostname()
    app.run(host="0.0.0.0", port=9610, debug=True, ssl_context=('/Users/yunfengchua/flask1/bin/flaskserver.crt','/Users/yunfengchua/flask1/bin/flaskserver.key'))
