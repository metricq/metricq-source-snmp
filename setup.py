from setuptools import setup

setup(
    name="metricq_source_snmp",
    version="0.2",
    author="TU Dresden",
    python_requires=">=3.10",
    packages=["metricq_source_snmp"],
    scripts=[],
    entry_points="""
      [console_scripts]
      metricq-source-snmp=metricq_source_snmp:run
      """,
    install_requires=["aiomonitor", "click", "click_log", "metricq ~= 4.0", "pysnmp"],
)
