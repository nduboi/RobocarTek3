#!/bin/bash
cd pc_dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main_pc.py --robot-ip 10.84.106.222 --log-level DEBUG