#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rospy
import os
import sys
import time
import yaml
from std_msgs.msg import Float32, Bool, String, UInt32

# micrometer
from mitsutoyo_instrument.msg import MitsutoyoMicrometer
from mitsutoyo_instrument.srv import GetMicrometerValue, GetMicrometerValueResponse
# tma
from auto_tma.tma402f3.tma402f3_interface import TMA402F3Interface
from netzsch_instrument.srv import NETZSCH_Measurement
# nextage
from nextage_nxa_interface.nextage_nxa_interface import NextageNXAInterface

tma_ip='192.168.0.20'
nextage_ip="192.168.0.23"


def wait_until_enter():
    print('Enter キーを押すまで待機...')
    input()
    print('proceed')


###############################################################
def main(tma_auto=True, tare_force=True, measure_mode=0, number_of_sample=2, gui_log_cb=None):
    # args
    # - tma_auto:
    #    - True  -> TMA実機の自動制御
    #    - False -> TMAは自動で動かない. 人が動作させる.
    # - tare_force:
    #    - False  -> skip tare_force()
    # - measure_mode:
    #    - 0 -> [AUTO]   自動gui制御でTMA測定をする
    #    - 1 -> [MANUAL] マニュアル操作でTMA測定をする
    #    - 2 -> [SKIP]   測定をskip
    #
    # status
    nextage_status = None  # {'preparing', 'ready', 'working' 'completed'}
    tma_status = 'waiting'  # {'waiting', 'in_operation', 'ready_to_pick_sample', 'ready_to_set_sample'}
    # variable (use for communication)
    ## written by nextage
    micrometer_counter  = 0
    set_sample_counter  = 0
    pick_sample_counter = 0
    assemble_counter    = 0
    disassemble_counter = 0
    ## wrriten by TMA process
    tma_process        = 0
    # variable (internal use)
    prev_thickness =    0

    # misc
    current_sample_number = 0  # 1始まり. サンプル1, サンプル2, ,,, サンプル10
    sample_id = 0  # 0始まり
    motion_speed = 100  # reduce if slow motion required

    # publisher
    pub_sample_id = rospy.Publisher('/mitsutoyo_micrometer/write/sample_id', UInt32, queue_size=1)
    msg_sample_id = UInt32()

    ###############################################################
    print('')
    print('########## Params ##########')
    print('tma_auto: %s'         % tma_auto)
    print('tare_force: %s'       % tare_force)
    print('measure_mode: %s'     % measure_mode)
    print('number_of_sample: %s' % number_of_sample)
    print('')
    # gui log
    if gui_log_cb:
        gui_log_cb('AutoTMA started')

    # error check
    if measure_mode not in (0, 1, 2):
        print('[ERROR] wrong arg. measure_mode: %s' % measure_mode)
        sys.exit(1)
    if number_of_sample not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10):
        print('[ERROR] wrong arg. number_of_sample: %s' % number_of_sample)
        sys.exit(1)

    ###############################################################
    print('')
    print('########## TMA init ##########')
    tma_if = TMA402F3Interface(tma_ip)
    tma_if.connect_tma()
    tma_if.reset_tma()

    ###############################################################
    print('')
    print('########## NEXTAGE init ##########')
    nx_if = NextageNXAInterface(nextage_ip)
    task_name = u"TMA load and unload (API)"
    total_num = number_of_sample
    var_names = [
        u"tma_process", u"tma_status",
        u"nextage_status",
        u"micrometer_counter",
        u"set_sample_counter", u"pick_sample_counter",
        u"assemble_counter", u"disassemble_counter",
        u"number_of_sample"
    ]

    print('Connecting to NEXTAGE')
    nx_if.setup(speed=motion_speed)  # get authority inside setup()
    nx_if.set_task(target_task_name=task_name)
    nx_if.servo_on()  # Servo ON
    nx_if.start_task()  # Start Task
    time.sleep(2)      # wait for initialization of variables in NEXTAGE

    # wait for ready
    print("waiting NEXTAGE becomes 'ready'")
    while (nx_if.get_var(u'nextage_status') != u'ready'):
        time.sleep(0.1)
        pass
    print("got 'ready', Let's go")

    # init_variable_via_plugin
    nx_if.set_var_socket("nextage_status", "preparing")
    nx_if.set_var_socket("tma_status", "waiting")
    nx_if.set_var_socket("micrometer_counter", 0)
    nx_if.set_var_socket("set_sample_counter", 0)
    nx_if.set_var_socket("pick_sample_counter", 0)
    nx_if.set_var_socket("assemble_counter", 0)
    nx_if.set_var_socket("disassemble_counter", 0)

    # initialize local variables
    prev_micrometer_counter  = nx_if.get_var('micrometer_counter')
    prev_set_sample_counter  = nx_if.get_var('set_sample_counter')
    prev_pick_sample_counter = nx_if.get_var('pick_sample_counter')
    prev_assemble_counter    = nx_if.get_var('assemble_counter')
    prev_disassemble_counter = nx_if.get_var('disassemble_counter')
    ##################################################################

    print('')
    print('########## start auto_tma ##########')
    print('Start auto_tma for %s samples'% number_of_sample)

    # check rosnode before process starts
    print('waiting for service servers')
    rospy.wait_for_service('/get_micrometer_value')  # service起動まで待つ
    if measure_mode == 0:
        rospy.wait_for_service('/netzsch_measurement_server')
    time.sleep(1)  # wait for rosnode init

    # start nextage motion
    ### [重要] NEXTAGEへは, 作るサンプルの個数(number_of_sample)を先に送り, プロセス開始指令(TMA_process)は後に送る必要がある.
    print("send start signal to NEXTAGE (number_of_sample: %s)"% total_num)
    nx_if.set_var_socket('number_of_sample', total_num)
    time.sleep(1)  # wait is neessary

    tma_process = 1
    print("send start signal to NEXTAGE (tma_process: 1)")
    nx_if.set_var_socket("tma_process", 1)
    time.sleep(1)  # wait is neessary
    ##################################################################

    # communication to nextage.
    tma_status = 'waiting'
    nx_if.set_var_socket("tma_status", tma_status)

    # initialize sample_id for micrometer database
    msg_sample_id.data = sample_id
    pub_sample_id.publish(msg_sample_id)

    # loop
    for i in range(number_of_sample+1):
        current_sample_number = i+1
        sample_id = i

        print('')
        print('########## start sample_id: %s measurement ########################'% sample_id)
        print('')
        print('########## micrometer measure (NEXTAGE) ##########')
        # 場合分け
        # i: 0-n (試行としては,n+1回で最後に一回サンプル回収動作がある)
        # i = 0-(n-1) -> thickness測定する
        # i = n       -> thickness測定しない

        if i==number_of_sample:
            print('skip micrometer')  # 最後のループではスキップ
        else:
            # wait until NEXTAGE counter updated
            while (prev_micrometer_counter == nx_if.get_var('micrometer_counter')):
                time.sleep(5)
                print("waiting for micrometer pushed (sample_id: %s)"% sample_id)
                pass
            prev_micrometer_counter = nx_if.get_var('micrometer_counter')
            print("got signal (micrometer) from nextage. Let's go.")

            while True:
                # service call
                try:
                    rospy.loginfo(f"try to get micrometer value with sample_id={sample_id}")
                    get_micrometer_value = rospy.ServiceProxy('/get_micrometer_value', GetMicrometerValue)
                    time.sleep(0.1)  # wait for registring
                    resp = get_micrometer_value(sample_id)
                    time.sleep(0.1)  # wait for registring

                    if(resp.success==True):
                        rospy.loginfo('thickness obtained')
                        thickness = resp.value
                        rospy.loginfo(f"thickness: {thickness}")

                        # display on gui
                        if gui_log_cb:
                            gui_log_cb('sample_id: %s, thickness: %s' % (sample_id, thickness))

                        # update sample_id for next sample
                        msg_sample_id.data = sample_id+1
                        pub_sample_id.publish(msg_sample_id)

                        break
                    else:
                        rospy.loginfo('thickness is not obtained')
                        time.sleep(10) # 10sごとに確認

                except KeyboardInterrupt:
                    print('ctrl+c')
                    sys.exit(1)
                except rospy.ServiceException as e:
                    rospy.logerr(f"Service call failed: {e}")


        print('')
        print('########## sample assemble (NEXTAGE) ##########')
        # communication to nextage.
        tma_status = 'waiting'
        nx_if.set_var_socket("tma_status", tma_status)

        # 場合分け
        # i: 0-n (試行としては,n+1回で最後に一回サンプル回収動作がある)
        # i = 0-(n-1) -> assemble
        # i = n         -> asesmbleしない
        if i==number_of_sample:
            print('skip assemble')
        else:
            # wait until NEXTAGE counter updated
            while (prev_assemble_counter == nx_if.get_var('assemble_counter')):
                time.sleep(5)
                print("waiting for sample assembled (sample_id: %s)"% sample_id)
                pass
            prev_assemble_counter = nx_if.get_var('assemble_counter')
            print("got signal (assemble) from nextage. Let's go.")

        # 以降の場合分け
        # i: 0-n (試行としては,n+1回で最後に一回サンプル回収動作がある)
        # i = 0       -> TMAopen, 前回サンプル無し,                               , pushrod初期化, 今回サンプルset, pushrod引張, TMAclose, 測定
        # i = 1-(n-1) -> TMAopen, 前回サンプル有り, pushrod緩める, 前回サンプルget, pushrod初期化, 今回サンプルset, pushrod引張, TMAclose, 測定
        # i = n       -> TMAopen, 前回サンプル有り, pushrod緩める, 前回サンプルget,              , 今回サンプル無し,           , TMAclose
        print('')
        print('########## TMA open (TMA) ##########')
        # communication to nextage.
        tma_status = 'in_operation'
        nx_if.set_var_socket("tma_status", tma_status)  # "do not work"

        if tma_auto:
            if i==0:
                tma_if.furnance_open_full()
                time.sleep(0.5)
            else:
                tma_if.furnance_open_full()
                time.sleep(0.5)
                tma_if.pushrod_up_sec(3)  # release tension from sample
                time.sleep(0.5)
        else:
            print('Please operate TMA manually')
            wait_until_enter()

        print('')
        print('########## sample pick (NEXTAGE) ##########')
        if tma_auto:
            if i==0:
                print('skip pick_sample (when i=0)')
            else:
                # communication to nextage.
                tma_status = 'ready_to_pick_sample'
                nx_if.set_var_socket("tma_status", tma_status)  # can work
                # wait until NEXTAGE counter updated
                while (prev_pick_sample_counter == nx_if.get_var('pick_sample_counter')):
                    time.sleep(5)
                    print("waiting for sample picked (sample_id: %s)"% (sample_id - 1))
                    pass
                prev_pick_sample_counter = nx_if.get_var('pick_sample_counter')
                print("got signal (pick_sample) from nextage. Let's go.")
        else:
            print('Please operate TMA manually')
            wait_until_enter()


        print('')
        print('########## pushrod adjust (TMA) ##########')
        # communication to nextage.
        tma_status = 'in_operation'
        nx_if.set_var_socket("tma_status", tma_status)  # "do not work"

        if tma_auto:
            if current_sample_number==number_of_sample+1:
                print('skip init_pushrod')
            else:
                tma_if.init_pushrod_for_sample_set(tare_force)
                time.sleep(0.5)
        else:
            print('Please operate TMA manually')
            wait_until_enter()


        print('')
        print('########## sample set (NEXTAGE) ##########')
        if tma_auto:
            if current_sample_number==number_of_sample+1:
                print('skip set_sample')
            else:
                # communication to nextage.
                tma_status = 'ready_to_set_sample'
                nx_if.set_var_socket("tma_status", tma_status)  # can work
                # wait until NEXTAGE counter updated
                while (prev_set_sample_counter == nx_if.get_var('set_sample_counter')):
                    time.sleep(5)
                    print("waiting for sample set (sample_id: %s)"% sample_id)
                    pass
                prev_set_sample_counter = nx_if.get_var('set_sample_counter')
                print("got signal (set_sample) from nextage. Let's go.")
                print("prev '%s', nextage '%s')"%(prev_set_sample_counter, nx_if.get_var('set_sample_counter')))
        else:
            print('Please operate TMA manually')
            wait_until_enter()


        print('')
        print('########## TMA close (TMA) ##########')
        # communication to nextage.
        tma_status = 'in_operation'
        nx_if.set_var_socket("tma_status", tma_status)  # "do not work"

        if tma_auto:
            if current_sample_number==number_of_sample+1:
                print('just close furnance')
                tma_if.furnance_close_full()
                time.sleep(0.5)
            else:
                tma_if.pushrod_down_sec(10)  # load pre-tension to sample. Enough time is required(6s is short). TMA stops automatically when enough pre-tension detected.
                time.sleep(0.5)
                tma_if.furnance_close_full()
                time.sleep(0.5)
        else:
            print('Please operate TMA manually')
            wait_until_enter()


        print('')
        print('########## sample measure (TMA) ##########')
        # communication to nextage.
        tma_status = 'in_operation'
        nx_if.set_var_socket("tma_status", tma_status)  # "do not work"

        if measure_mode == 0 or measure_mode == 1:
            if measure_mode == 0:
                print('measure_mode: [AUTO]')
            elif measure_mode == 1:
                print('measure_mode: [MANUAL]')
                print('Please measure TMA manually')

            if current_sample_number==number_of_sample+1:
                print('skip measurement')
            else:
                # register service
                if measure_mode == 0:
                    rospy.wait_for_service("/netzsch_measurement_server")
                    netzsch_measurement_server = rospy.ServiceProxy("/netzsch_measurement_server", NETZSCH_Measurement)
                elif measure_mode == 1:
                    rospy.wait_for_service("/netzsch_measurement_server_mock")
                    netzsch_measurement_server = rospy.ServiceProxy("/netzsch_measurement_server_mock", NETZSCH_Measurement)

                # wait for result
                while not rospy.is_shutdown():
                    try:
                        # service call in every loop
                        rospy.loginfo(f"try to measure with sample_id={sample_id}")
                        resp = netzsch_measurement_server(sample_id=sample_id, sample_thickness=thickness)

                        if(resp.success==True):
                            rospy.loginfo('measurement succeeded')
                            rospy.loginfo(f"success={resp.success}, message={resp.message}")
                            break
                        else:
                            rospy.loginfo('under measurement')
                            rospy.loginfo(f"success={resp.success}, message={resp.message}")
                            rospy.sleep(10) # 10sごとに確認

                    except rospy.ServiceException as e:
                        rospy.logerr(f"Service call failed: {e}")
                        rospy.sleep(1)

        elif measure_mode == 2:
            print('measure_mode: [SKIP]')
        else:
            print('wrong arg. measure_mode: %s' % measure_mode)

        # communication to nextage.
        tma_status = 'measure_completed'
        nx_if.set_var_socket("tma_status", tma_status)

        print('')
        print('############ Result of sample_id: %s ############' % sample_id)
        print('thickness:', thickness)
        print('########################################')

    # check disassemble_counter here if necessary
    print('')
    print('########## end of whole TMA process ##########')
    tma_if.reset_tma()  # reset TMA
    if gui_log_cb:
        gui_log_cb('AutoTMA finished')


if __name__ == "__main__":
    rospy.init_node("auto_tma", disable_signals=True)
    #main(tma_auto=True, tare_force=False, measure_mode=2, number_of_sample=2)
    #main(tma_auto=True, tare_force=False, measure_mode=0, number_of_sample=2)
    #main(tma_auto=True, tare_force=True, measure_mode=2)
    main(tma_auto=True, tare_force=True, measure_mode=0, number_of_sample=2)
