# Basic script to kill all old bars and launch new.

# Terminate already running bad instances
killall -q polybar
sleep 1

if type "xrandr"; then
  #存在xrandr时，对每个屏重新加载一次polybar
  for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
    MONITOR=$m polybar --reload main_bar &
  done
else
  polybar --reload main_bar &
fi

