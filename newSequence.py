# coding: UTF-8

#-------------------------------------------------------------------------------
# Name:        sequence
# Purpose:      sequence all functions
#
# Author:      kitawaki
#
# Created:     31/08/2016
# Copyright:   (c) kitawki 2016
# Licence:     <your licence>
#
#-------------------------------------------------------------------------------

import recognition as rcg
import action as act
import stop as stop
import userutility as utl
import copy
import sys
#-----------------------------------------------------------------------------#
# Declation                                                                  #
#-----------------------------------------------------------------------------#
# グローバル定数
# 状態
GLOBAL_INITIAL_MODE = 0    # 初期状態
GLOBAL_SEARCH_MODE  = 1    # 探索状態
GLOBAL_FAST_MODE    = 2    # 最速走行状態
GLOBAL_GOAL_MODE    = 3    # ゴール状態
# 方向
GLOBAL_EAST         = 1
GLOBAL_NORTH        = 2
GLOBAL_WEST         = 3
GLOBAL_SOUTH        = 4
# 初期状態
GLOBAL_INITIAL_POSITION  = [0,0]
GLOBAL_INITIAL_WALL_INFO = 13
GLOBAL_INITIAL_DIRECTION = GLOBAL_NORTH

# グローバル変数
global_maze      = utl.Maze()                   # 迷路インスタンス
global_position  = GLOBAL_INITIAL_POSITION      # 現在座標
global_direction = GLOBAL_INITIAL_DIRECTION     # 現在の方向
global_was_moved = True                         # 区画移動が終了時はTrue

#タクトスイッチ押した判定用のカウンタ
swstatecnt = [0,0,0]

# 壁情報のビット表現
RIGHT  = 0b00000001
TOP    = 0b00000010
LEFT   = 0b00000100
BOTTOM = 0b00001000

# 距離情報取得用
FRONT_DIRECTION     = 0             # 前方
LEFT_DIRECTION      = 1             # 左方
RIGHT_DIRECTION     = 2             # 右方

ROTATERIGHT = -88
ROTATELEFT = 88
ROTATEOPPOSIT = 175

#-----------------------------------------------------------------------------#
# Functions                                                                  #
#-----------------------------------------------------------------------------#

def selectMode(presentMode, presentPosition, goalPositions):
    '''
    状態遷移関数selectModeの概要
    入力:現在の状態，現在の位置，ゴール位置のリスト
    出力:遷移後の状態
    タクトスイッチ0を押すと初期状態へ遷移
    タクトスイッチ1を押すと初期状態のときは探索状態へ遷移するが，
    ゴール状態のときは最速走行状態へ遷移し，それ以外の状態では遷移なし
    タクトスイッチ2を押すとプログラム終了
    '''
    mode = presentMode

    # タクトスイッチのスイッチ取得
    swState = rcg.get_switch_state()
    
    # スイッチ情報による遷移
    if swState[0] == 1:
        mode = GLOBAL_INITIAL_MODE
    elif swState[1] == 1:
        if presentMode == GLOBAL_INITIAL_MODE:
            mode = GLOBAL_SEARCH_MODE
        elif presentMode == GLOBAL_GOAL_MODE:
            mode = GLOBAL_FAST_MODE
    elif swState[2] == 1:
        print "Sequence is killed by using switch"
        act.led([0,0,0,0])
        act.buzzer(0)
        sys.exit()
    
    # ゴール到達による遷移
    if (presentMode in [GLOBAL_SEARCH_MODE, GLOBAL_FAST_MODE]) \
    and (presentPosition in goalPositions):
        mode = GLOBAL_GOAL_MODE
    
    return mode

def rcgWall2mazeWall(presentDirection,rcgWallInfo):
    directionForConvert = TOP
    if presentDirection == GLOBAL_EAST:
        directionForConvert = RIGHT
    elif presentDirection == GLOBAL_NORTH:
        directionForConvert = TOP
    elif presentDirection == GLOBAL_WEST:
        directionForConvert = LEFT
    elif presentDirection == GLOBAL_SOUTH:
        directionForConvert = BOTTOM
    else:
        print "An error occurs in rcgWall2mazeWall function"
    
    change_the_world(directionForConvert,rcgWallInfo)
    return mazeWallInfo


def change_the_world(mydirection, local_wallinfo):
    global_wallinfo = 0
    #print "mydirectionC=",mydirection
    #print "local_wallinfoC",local_wallinfo
    bit0 = ( local_wallinfo & 0b0001 ) >> 0
    bit1 = ( local_wallinfo & 0b0010 ) >> 1
    bit2 = ( local_wallinfo & 0b0100 ) >> 2 
    bit3 = ( local_wallinfo & 0b1000 ) >> 3
    
    if mydirection == RIGHT:
        new0 = bit1
        new1 = bit2
        new2 = bit3
        new3 = bit0
    elif mydirection == TOP:
        new0 = bit0
        new1 = bit1
        new2 = bit2
        new3 = bit3
    elif mydirection == LEFT:
        new0 = bit3
        new1 = bit0
        new2 = bit1
        new3 = bit2
    elif mydirection == BOTTOM:
        new0 = bit2
        new1 = bit3
        new2 = bit0
        new3 = bit1

    global_wallinfo = global_wallinfo | ( new0 << 0 )
    global_wallinfo = global_wallinfo | ( new1 << 1 )
    global_wallinfo = global_wallinfo | ( new2 << 2 )
    global_wallinfo = global_wallinfo | ( new3 << 3 )
    return global_wallinfo


def main():
    '''
    マイクロマウスマシンの起動プログラム関数
    入出力なし
    '''
    global global_position

    print "Main function is called"
    mode = GLOBAL_INITIAL_MODE
    
    while True:
        # 状態ごとの動作切り替え
        if mode == GLOBAL_INITIAL_MODE:
            initialModeFunction()
        elif mode == GLOBAL_SEARCH_MODE:
            searchModeFunction()
        elif mode == GLOBAL_FAST_MODE:
            fastModeFunction()
        elif mode == GLOBAL_GOAL_MODE:
            goalModeFunction()
        else:
            act.led([1,1,1,1])
            print "You are in undefined mode"

        # 状態の遷移と表示
        presentMode = mode
        mode = selectMode(presentMode, global_position, utl.goal)
        if presentMode != mode:
            if mode == GLOBAL_INITIAL_MODE:
                act.led([1,0,0,0])
                print "Mode changed to INITIAL MODE"
            elif mode == GLOBAL_SEARCH_MODE:
                act.led([0,1,0,0])
                print "Mode changed to SEARCH MODE"
            elif mode == GLOBAL_FAST_MODE:
                act.led([0,0,1,0])
                print "Mode changed to FAST MODE"
            elif mode == GLOBAL_GOAL_MODE:
                act.led([0,0,0,1])
                print "Mode changed to GOAL MODE"
            else:
                act.led([1,1,1,1])
                print "Mode changed to UNDEFINED MODE"


#--------------------------------------------------------------#
# 初期状態の動作関数
#--------------------------------------------------------------#
def initialModeFunction():
    global global_maze, global_position, global_direction
    # モータへの停止命令
    stop.stop()
    # 迷路インスタンスのリセット
    global_maze = utl.Maze()
    # 座標のリセット
    global_position = GLOBAL_INITIAL_POSITION
    # 方向のリセット
    global_direction = GLOBAL_INITIAL_DIRECTION

#--------------------------------------------------------------#
# 探索状態の動作関数
#--------------------------------------------------------------#
def searchModeFunction():
    global global_maze, global_position, global_direction
    if global_position == GLOBAL_INITIAL_POSITION:
        # 最初は半歩前進後に座標更新
        half_step()     # half_stepは動作終了まで処理を専有する関数
        global_position = [0,1]
    elif global_position == utl.goal:
        # 最後は半歩前進
        half_step()     # half_stepは動作終了まで処理を専有する関数
    else:
        # 壁情報のセット
        wallInfoFromRcg = rcg.check_wall()
        wallInfoForMaze = rcgWall2mazeWall(global_direction, wallInfoFromRcg)
        global_maze.set_wallinfo(global_position,wallInfoForMaze)
        # 次に進む座標を取得
        global_maze.adachi()
        nextPosition = global_maze.get_nextpos(global_position)
        # blockMoveは動作終了まで処理を専有する関数
        global_direction = blockMove(global_position, nextPosition, global_direction)
        # 移動命令終了後は座標更新
        global_position = nextPosition

#--------------------------------------------------------------#
# 最速走行状態の動作関数
#--------------------------------------------------------------#
def fastModeFunction():
    # 最初の処理
    # 最後の処理
    # 最初と最後以外の処理
    print "FAST MODE is not implemented"

#--------------------------------------------------------------#
# ゴール状態の動作関数
#--------------------------------------------------------------#
def goalModeFunction():
    # モータへの停止命令
    stop.stop()

#--------------------------------------------------------------#
# ブロック移動関数
#--------------------------------------------------------------#
def blockMove(presentPosition, nextPosition, presentDirection):
    '''
    入力:現在座標，移動後座標，現在方向
    出力:移動後方向
    '''
    xDist = nextPosition[0] - presentPosition[0]
    yDist = nextPosition[1] - presentPosition[1]
    if (xDist != 0) and (yDist != 0):
        print "An error occurs in blcokMove function"
        nextDirection = presentDirection
    else:
        # x方向の移動
        if xDist != 0:
            if xDist > 0:
                nextDirection = GLOBAL_EAST
                if presentDirection == GLOBAL_EAST:
                    goRotateGo(0,0,1)
                elif presentDirection == GLOBAL_NORTH:
                    goRotateGo(0.5,-90,0.5)
                elif presentDirection == GLOBAL_WEST:
                    goRotateGo(0,180,0)
                elif presentDirection == GLOBAL_SOUTH:
                    goRotateGo(0.5,90,0.5)
            elif xDist < 0:
                nextDirection = GLOBAL_WEST
                if presentDirection == GLOBAL_EAST:
                    goRotateGo(0,180,0)
                elif presentDirection == GLOBAL_NORTH:
                    goRotateGo(0.5,90,0.5)
                elif presentDirection == GLOBAL_WEST:
                    goRotateGo(0,0,1)
                elif presentDirection == GLOBAL_SOUTH:
                    goRotateGo(0.5,-90,0.5)
        else:
            nextDirection = presentDirection
        
        # y方向の移動
        presentDirection = nextDirection
        if yDist != 0:
            if yDist > 0:
                nextDirection = GLOBAL_NORTH
                if presentDirection == GLOBAL_EAST:
                    goRotateGo(0.5,90,0.5)
                elif presentDirection == GLOBAL_NORTH:
                    goRotateGo(0,0,1)
                elif presentDirection == GLOBAL_WEST:
                    goRotateGo(0.5,-90,0.5)
                elif presentDirection == GLOBAL_SOUTH:
                    goRotateGo(0,180,0)
            elif yDist < 0:
                nextDirection = GLOBAL_SOUTH
                if presentDirection == GLOBAL_EAST:
                    goRotateGo(0.5,-90,0.5)
                elif presentDirection == GLOBAL_NORTH:
                    goRotateGo(0,180,0)
                elif presentDirection == GLOBAL_WEST:
                    goRotateGo(0.5,90,0.5)
                elif presentDirection == GLOBAL_SOUTH:
                    goRotateGo(0,0,1)
        else:
            nextDirection = presentDirection
    
    return nextDirection


#--------------------------------------------------------------#
# 直進走行+回転走行+直進走行関数
#--------------------------------------------------------------#
def goRotateGo(blockDistance1,degreeAngle,blockDistance2):
    # 直進1
    dist = rcg.get_distance()
    dist[FRONT_DIRECTION] = -1
    act.go_straight(blockDistance1,dist[FRONT_DIRECTION],dist[LEFT_DIRECTION],dist[RIGHT_DIRECTION])
    while act.is_running():
        dist = rcg.get_distance()
        dist[FRONT_DIRECTION] = -1
        act.keep_order(dist[FRONT_DIRECTION],dist[LEFT_DIRECTION],dist[RIGHT_DIRECTION])
    
    # 回転
    act.rotate(degreeAngle)
    while act.is_running():
        act.keep_order(-1,-1,-1)
    
    # 直進2
    dist = rcg.get_distance()
    dist[FRONT_DIRECTION] = -1
    act.go_straight(blockDistance2,dist[FRONT_DIRECTION],dist[LEFT_DIRECTION],dist[RIGHT_DIRECTION])
    while act.is_running():
        dist = rcg.get_distance()
        dist[FRONT_DIRECTION] = -1
        act.keep_order(dist[FRONT_DIRECTION],dist[LEFT_DIRECTION],dist[RIGHT_DIRECTION])


#--------------------------------------------------------------#
#--------------------------------------------------------------#
def half_step():
    distance = rcg.get_distance()
    distance[FRONT_DIRECTION] = -1
##  distance[LEFT_DIRECTION] = -1
##  distance[RIGHT_DIRECTION] = -1
    # 0.5マス前進
    act.go_straight(0.60,distance[FRONT_DIRECTION],distance[LEFT_DIRECTION],distance[RIGHT_DIRECTION])
    # 0.5マス進み終わるまで待機
    while True:
        distance = rcg.get_distance()
        distance[FRONT_DIRECTION] = -1
        act.keep_order(distance[FRONT_DIRECTION],distance[LEFT_DIRECTION],distance[RIGHT_DIRECTION])
        if not(act.is_running()):
            break
    return True


if __name__ == '__main__':
    main()
