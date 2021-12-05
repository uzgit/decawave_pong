#!/usr/bin/python3

import turtle
import paho.mqtt.client as mqtt

import argparse
import time

parser = argparse.ArgumentParser()
parser.add_argument("-s", "--address", type=str, default="192.168.1.100", help="address of mqtt server")
parser.add_argument("-p", "--port", type=str, default="1883", help="port of mqtt server")
parser.add_argument("-l", "--left", type=str, default="5625", help="ID of left paddle node")
parser.add_argument("-r", "--right", type=str, default="16d2", help="ID of right paddle node")
parser.add_argument("-d", "--dimension", type=str, default="x", help="dimension of node control motion (x,y, or z)")
parser.add_argument("--min", type=int, default=0, help="min position")
parser.add_argument("--max", type=int, default=1.98, help="max position")

arguments = vars(parser.parse_args())

for parameter, value in arguments.items():
    print(f"{parameter} : {value}")

print(f"Left paddle ID: {arguments['left']}, right paddle ID: {arguments['right']}")
print(f"Connecting to MQTT server at {arguments['address']}:{arguments['port']}...")

positions = [0, 0]

def constrain(value, minimum, maximum):
    
    result = value

    if( result < minimum ):
        result = minimum
    elif( result > maximum ):
        result = maximum

    return maximum

def interpolate(value, min1, max1, min2, max2):

    result = value - min1
    result /= max1 - min1
    result *= max2 - min2
    result += min2

#    result = min2 + (max2 - min2) * (value - min1) / (max1 - min1)

#    result = constrain(result, min2, max2)

#    print(f"{value} in [{min1}, {max1}] going to {result} in [{min2}, {max2}]")

    return result

# init
################################################################
score_a = 0
score_b = 0

screen = turtle.Screen()
screen.title("Pong")
screen.bgcolor("black")
screen.setup(width=800, height=600)
screen.tracer(0)

paddle_a = turtle.Turtle()
paddle_a.speed(0)
paddle_a.shape("square")
paddle_a.color("white")
paddle_a.shapesize(stretch_wid=5, stretch_len=1)
paddle_a.penup()
paddle_a.goto(-350, 0)

paddle_b = turtle.Turtle()
paddle_b.speed(0)
paddle_b.shape("square")
paddle_b.color("white")
paddle_b.shapesize(stretch_wid=5, stretch_len=1)
paddle_b.penup()
paddle_b.goto(350, 0)

ball = turtle.Turtle()
ball.speed(0)
ball.shape("circle")
ball.color("white")
ball.penup()
ball.goto(0, 0)
ball.dx = 0.1
ball.dy = -0.1

pen = turtle.Turtle()
pen.speed(0)
pen.color("white")
pen.penup()
pen.hideturtle()
pen.goto(0, 260)
#pen.write("Player A: 0  Player B: 0", align="center", font=("Courier", 20, "normal"))

#def paddle_a_up():
#    y = paddle_a.ycor()
#    y += 30
#    paddle_a.sety(y)
#
#def paddle_a_down():
#    y = paddle_a.ycor()
#    y -= 30
#    paddle_a.sety(y)
#
#def paddle_b_up():
#    y = paddle_b.ycor()
#    y += 30
#    paddle_b.sety(y)
#
#def paddle_b_down():
#    y = paddle_b.ycor()
#    y -= 30
#    paddle_b.sety(y)
#
#screen.listen()
#screen.onkeypress(paddle_a_up, "w")
#screen.onkeypress(paddle_a_down, "s")
#screen.onkeypress(paddle_b_up, "Up")
#screen.onkeypress(paddle_b_down, "Down")

################################################################

# mqtt stuff
################################################################
def on_connect(mqttc, obj, flags, rc):
    print("rc: "+str(rc))

def on_message(mqttc, obj, msg):
    global positions

    print(msg.topic+" "+str(msg.qos)+" "+str(msg.payload), end=": ")

    topic_name = msg.topic
    position = eval(msg.payload)["position"][arguments["dimension"]]

#    position = interpolate( position, 0, 1.98, -100, 100 )
#    position = int(position)

    if( arguments["left"] in topic_name ):
        positions[0] = position
    elif( arguments["right"] in topic_name ):
        positions[1] = position
    else:
        print("I don't recognize this message!")

def on_publish(mqttc, obj, mid):
    print("mid: "+str(mid))

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: "+str(mid)+" "+str(granted_qos))

def on_log(mqttc, obj, level, string):
    print(string)

mqttc = mqtt.Client()
mqttc.on_message = on_message
mqttc.on_connect = on_connect
mqttc.on_publish = on_publish
mqttc.on_subscribe = on_subscribe
mqttc.connect("192.168.1.100", 1883, 60)
mqttc.subscribe("dwm/node/5625/uplink/location", 0)
mqttc.subscribe("dwm/node/16d2/uplink/location", 0)
mqttc.loop_start()
################################################################

# game loop
################################################################
while True:


    try:
        int_position_a = interpolate( positions[0], 0.5, 1.5, -300, 300 )
        int_position_b = interpolate( positions[1], 0.5, 1.5, -300, 300 )
    except:
        print("oops")

#    print(f"left: {positions[0]}, right: {positions[1]}")
#    print(f"left: {int_position_a}, right: {int_position_b}")

    paddle_a.sety(int_position_a)
    paddle_b.sety(int_position_b)

    screen.update()

    # move the ball
    ball.setx(ball.xcor() + ball.dx)
    ball.sety(ball.ycor() + ball.dy)

    # border checking
    if ball.ycor() > 280:
        ball.sety(280)
        ball.dy *= -1

    if ball.ycor() < -280:
        ball.sety(-280)
        ball.dy *= -1

    #left and right
    if (ball.xcor() < -340 and ball.xcor() > -350) and (paddle_a.ycor() + 50 > ball.ycor() > paddle_a.ycor() - 50):
        score_a += 1
        pen.clear()
#        pen.write("Player A: {} Player B: {}".format(score_a, score_b), align="center", font=("Courier", 20, "normal"))
    if ball.xcor() > 380:
        score_a = 0
        pen.clear()
#        pen.write("Player A: {} Player B: {}".format(score_a, score_b), align="center", font=("Courier", 20, "normal"))
        ball.goto(0, 0)
        ball.dx *= -1


    if (ball.xcor() > 340 and ball.xcor() < 350) and (paddle_b.ycor() + 50 > ball.ycor() > paddle_b.ycor() - 50):
        score_b += 1
        pen.clear()
#        pen.write("Player A: {} Player B: {}".format(score_a, score_b), align="center", font=("Courier", 20, "normal"))
    if ball.xcor() < -380:
        score_b = 0
        pen.clear()
#        pen.write("Player A: {} Player B: {}".format(score_a, score_b), align="center", font=("Courier", 20, "normal"))
        ball.goto(0, 0)
        ball.dx *= -1


    # paddle and ball collisions
    if (ball.xcor() > 340 and ball.xcor() < 350) and (paddle_b.ycor() + 50 > ball.ycor() > paddle_b.ycor() - 50):
        ball.setx(340)
        ball.dx *= -1

    if (ball.xcor() < -340 and ball.xcor() > -350) and (paddle_a.ycor() + 50 > ball.ycor() > paddle_a.ycor() - 50):
        ball.setx(-340)
        ball.dx *= -1
