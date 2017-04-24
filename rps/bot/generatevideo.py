from moviepy.editor import *
from moviepy.video.tools.drawing import circle

import os
from tempfile import mkstemp


def vText(winner_screen_name, loser_screen_name, winner_rhs = True):
    if winner_rhs:
        rhs = "@" + winner_screen_name
        lhs = "@" + loser_screen_name
    else:
        lhs = "@" + winner_screen_name
        rhs = "@" + loser_screen_name
    return rhs + "    v    " + lhs

def wText(winner_screen_name):
    return "Winner\n@" + winner_screen_name + "\n"

def duelFilename(
            winner_screen_name,
            winner_rpc,
            loser_screen_name,
            loser_rpc,
            hashtext,
            winner_rhs = True):
    short_name = {'Rock': 'R', 'Paper': 'P', 'Scissors': 'S'}
    path_videos = 'bot/templates/videos/'
    if winner_rhs:
        duel_filename = path_videos + short_name[winner_rpc] + '-' + short_name[loser_rpc] + '.mp4'
    else:
        duel_filename = path_videos + short_name[loser_rpc] + '-' + short_name[winner_rpc] + '.mp4'
    return duel_filename

def makeVideoRPS(
            gif_filename,
            winner_screen_name,
            winner_rpc,
            loser_screen_name,
            loser_rpc,
            hashtext,
            winner_rhs = True):

    duel_filename=duelFilename(winner_screen_name,
                                winner_rpc,
                                loser_screen_name,
                                loser_rpc,
                                hashtext,
                                winner_rhs)
            
    duel = VideoFileClip(duel_filename).add_mask()
    
    w,h = duel.size
    duel.mask.get_frame = lambda t: circle(screensize=(duel.w,duel.h),
                                           center=(duel.w/2,duel.h/4),
                                           radius=max(0,int(1000-200*t)),
                                           col1=1, col2=0, blur=4)
    v_text = vText(winner_screen_name, loser_screen_name, winner_rhs)
    v = TextClip(v_text,fontsize=30,font='Xolonium-Bold',color='yellow')
    v = v.set_pos('center').set_duration(1)
    v_sized  = CompositeVideoClip( [v.set_pos('center')], size=(w,h))
    
    bot = TextClip("#RockPaperScissors referee: @RPSrobot ", font="Amiri-Bold", fontsize=20, color="white")
    bot = bot.set_duration(3.5)
    bot = CompositeVideoClip( [bot.set_pos(("right","top"))], size=(w,h))
    
    
    winner = TextClip(wText(winner_screen_name), font="Amiri-bold", color="red",
                       fontsize=60)
    winner_end = winner.set_duration(1)
    winner_end_sized  = CompositeVideoClip( [winner_end.set_pos(("center","bottom"))], size=(w,h))
    
    winner_mask = winner.set_duration(duel.duration)
    
    final = CompositeVideoClip([winner_mask.set_pos(("center","bottom")),duel],
                               size =duel.size)
    
    duel_bot = CompositeVideoClip([final, bot])
    final_clip = concatenate_videoclips([v_sized, duel_bot, winner_end_sized]).resize(width=496)
    final_clip .write_gif(gif_filename, fps=10)

def main():

    # Open a file
    fd, path = mkstemp(suffix='.gif')
    makeVideoRPS(
            gif_filename = path,
            winner_screen_name='Twitter_A',
            winner_rpc='Rock',
            loser_screen_name='Twitter_B',
            loser_rpc='Scissors',
            hashtext='#Example',
            winner_rhs = True)
    # Close opened file
    print(path)
    s = input('--> ')
    os.close( fd )
    os.remove(path)


if __name__ == '__main__':
    main()
