#!/bin/bash
sort hashtags > hashtags.new
cat hashtags.new | uniq -c | less
echo hashtags.new

