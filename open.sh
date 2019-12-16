#!/bin/bash

cat open.txt | while read line
do
    open ./images/${line}.png &
    sleep 8
done
