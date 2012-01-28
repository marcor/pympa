#!/usr/bin/env python
# -*- coding: ISO-8859-1 -*-

# pympa.py is part of Pympa.
# Copyright (C) 2006 by Marco Rimoldi
# Released under the GNU General Public License
# (See the included COPYING file)
#
# Pympa is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pympa is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pympa; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import os, time
import mpalib
import wx

ID_ERASE = wx.NewId()
ID_LOAD = wx.NewId()
ID_APPEND_TRACK = wx.NewId()
ID_INSERT_TRACK = wx.NewId()
ID_REMOVE_TRACK = wx.NewId()
ID_SPLIT_FILE = wx.NewId()
ID_TRACK_BEGIN = wx.NewId()
ID_TRACK_TITLE = wx.NewId()
ID_TRACK_END = wx.NewId()

wildcard = "Mpeg Audio Files (*.mpa;*.mp1;*.mp2;*.mp3)|*.mpa;*.mp1;*.mp2;*.mp3"
ALL = "(all files)"
VARIOUS = "%"   # string used in id3 fields to represent multiple values
round = lambda f: int(f + 0.5)

#227: self.SetMinSize((470, 435))
#90: self.genre_field = wx.Choice(self.id3_tab, -1, choices=[], style=wx.CB_SORT)

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class MyLog(wx.PyLog):

    def __init__(self, textCtrl, logTime=0):
    #--------------------------------------
        wx.PyLog.__init__(self)
        self.tc = textCtrl
        self.logTime = logTime

    def DoLogString(self, message, timeStamp):
    #----------------------------------------
        if self.tc:
            self.tc.AppendText(message)


class TextField(wx.TextCtrl):

    def __init__(self, parent, id, value="", alpha=True, length=30, size=(-1,-1)):
    #--------------------------------------------------------------
        wx.TextCtrl.__init__(self, parent, id, value, size=size)
        self.SetMaxLength(length)
        if not alpha: # input should be filtered
            self.Bind(wx.EVT_KEY_DOWN, self.FilterInput)

    def FilterInput(self, event):
    #---------------------------
        key = event.GetKeyCode()
        # we filter anything that is not a digit or a backspace
        if key in range(48, 58) or key in range(326, 336) or key in (8, 127, wx.WXK_LEFT, wx.WXK_RIGHT):
            event.Skip()

class TimeField(TextField):

    def __init__(self, parent, id, value="", length=9, size=(-1,-1)):
    #--------------------------------------------------------------
        TextField.__init__(self, parent, id, value, True, length, size)

    def FilterInput(self, event):
    #---------------------------
        key = event.GetKeyCode()
        wx.LogMessage("key code: %d\n" % key)
        if key in range(48, 58) or key in range(326, 336) or key in (8, 46, 127, wx.WXK_LEFT, wx.WXK_RIGHT):
            event.Skip()

class Track:
    pass

class MyFrame(wx.Frame):

    def __init__(self, *args, **kwds):
    #--------------------------------
        # begin wxGlade: MyFrame.__init__
        kwds["style"] = wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.notebook = wx.Notebook(self, -1, style=0)
        self.split_tab = wx.Panel(self.notebook, -1)
        self.id3_tab = wx.Panel(self.notebook, -1)
        self.info_tab = wx.Panel(self.notebook, -1)
        self.info_sizer_staticbox = wx.StaticBox(self.info_tab, -1, "Info")
        self.xing_sizer_staticbox = wx.StaticBox(self.info_tab, -1, "Xing Header")
        self.taginfo_sizer_staticbox = wx.StaticBox(self.id3_tab, -1, "TagInfo")
        self.options_sizer_staticbox = wx.StaticBox(self.id3_tab, -1, "Options")
        self.track_sizer_staticbox = wx.StaticBox(self.split_tab, -1, "Track")
        self.editor_sizer_staticbox = wx.StaticBox(self.split_tab, -1, "Editor")
        self.choice_sizer_staticbox = wx.StaticBox(self.info_tab, -1, "Current File")

        # Menu Bar
        self.main_frame_menubar = wx.MenuBar()
        self.SetMenuBar(self.main_frame_menubar)
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(wx.ID_OPEN, "Open...", "", wx.ITEM_NORMAL)
        wxglade_tmp_menu.AppendSeparator()
        wxglade_tmp_menu.Append(wx.ID_EXIT, "Exit", "", wx.ITEM_NORMAL)
        self.main_frame_menubar.Append(wxglade_tmp_menu, "File")
        wxglade_tmp_menu = wx.Menu()
        wxglade_tmp_menu.Append(wx.ID_ABOUT, "About", "", wx.ITEM_NORMAL)
        self.main_frame_menubar.Append(wxglade_tmp_menu, "?")
        # Menu Bar end
        self.file_choice = wx.Choice(self.info_tab, -1, choices=[], style=wx.CB_SORT)
        self.info = wx.StaticText(self.info_tab, -1, "")
        self.xing = wx.StaticText(self.info_tab, -1, "")
        self.reloadbtn = wx.Button(self.info_tab, ID_LOAD, "Reload!")
        self.openbtn = wx.Button(self.info_tab, wx.ID_OPEN, "Open...")
        self.track_label = wx.StaticText(self.id3_tab, -1, "Track:", style=wx.ALIGN_RIGHT)
        self.track_field = TextField(self.id3_tab, -1, length=2, alpha=False)
        self.title_label = wx.StaticText(self.id3_tab, -1, "Title:", style=wx.ALIGN_RIGHT)
        self.title_field = TextField(self.id3_tab, -1, "")
        self.artist_label = wx.StaticText(self.id3_tab, -1, "Artist:", style=wx.ALIGN_RIGHT)
        self.artist_field = TextField(self.id3_tab, -1, "")
        self.album_label = wx.StaticText(self.id3_tab, -1, "Album:", style=wx.ALIGN_RIGHT)
        self.album_field = TextField(self.id3_tab, -1, "")
        self.year_label = wx.StaticText(self.id3_tab, -1, "Year:", style=wx.ALIGN_RIGHT)
        self.year_field = TextField(self.id3_tab, -1, length=4, alpha=False)
        self.genre_label = wx.StaticText(self.id3_tab, -1, "Genre:", style=wx.ALIGN_RIGHT)
        self.genre_field = wx.Choice(self.id3_tab, -1, choices=[], style=wx.CB_SORT)
        self.comment_label = wx.StaticText(self.id3_tab, -1, "Comment:", style=wx.ALIGN_RIGHT)
        self.comment_field = TextField(self.id3_tab, -1, "")
        self.check_comment_adjust = wx.CheckBox(self.id3_tab, -1, "Auto-adjust comment length")
        self.erase_btn = wx.Button(self.id3_tab, ID_ERASE, "Erase!")
        self.save_btn = wx.Button(self.id3_tab, wx.ID_SAVE, "Save!")
        self.track_choice = wx.Choice(self.split_tab, -1, choices=[])
        self.split_label_1 = wx.StaticText(self.split_tab, -1, "Total tracks:")
        self.tracks_number_label = wx.StaticText(self.split_tab, -1, "0")
        self.track_title_label = wx.StaticText(self.split_tab, -1, "Title:", style=wx.ALIGN_RIGHT)
        self.track_title_field = TextField(self.split_tab, ID_TRACK_TITLE, "")
        self.begin_label = wx.StaticText(self.split_tab, -1, "Beginning:", style=wx.ALIGN_RIGHT)
        self.begin_field = TimeField(self.split_tab, ID_TRACK_BEGIN, "")
        self.label_11 = wx.StaticText(self.split_tab, -1, "frame:", style=wx.ALIGN_RIGHT)
        self.begin_frame_label = wx.StaticText(self.split_tab, -1, "")
        self.end_label = wx.StaticText(self.split_tab, -1, "End:", style=wx.ALIGN_RIGHT)
        self.end_field = TimeField(self.split_tab, ID_TRACK_END, "")
        self.label_12 = wx.StaticText(self.split_tab, -1, "frame:", style=wx.ALIGN_RIGHT)
        self.end_frame_label = wx.StaticText(self.split_tab, -1, "")
        self.static_line_1 = wx.StaticLine(self.split_tab, -1)
        self.label_7 = wx.StaticText(self.split_tab, -1, "Total frames:")
        self.frames_label = wx.StaticText(self.split_tab, -1, "")
        self.label_8 = wx.StaticText(self.split_tab, -1, "Actual playing time:")
        self.time_label = wx.StaticText(self.split_tab, -1, "")
        self.append_btn = wx.Button(self.split_tab, ID_APPEND_TRACK, "Append")
        self.insert_btn = wx.Button(self.split_tab, ID_INSERT_TRACK, "Insert")
        self.remove_btn = wx.Button(self.split_tab, ID_REMOVE_TRACK, "Remove")
        self.split_btn = wx.Button(self.split_tab, ID_SPLIT_FILE, "Split...")
        self.logwindow = wx.TextCtrl(self, -1, "", style=wx.TE_MULTILINE|wx.TE_READONLY)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_MENU, self.OnOpenFile, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnMenuExit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self.OnShowAbout, id=wx.ID_ABOUT)
        self.Bind(wx.EVT_CHOICE, self.OnFileSelect, self.file_choice)
        self.Bind(wx.EVT_BUTTON, self.ReloadSelectedFile, id=ID_LOAD)
        self.Bind(wx.EVT_BUTTON, self.OnOpenFile, id=wx.ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.OnEraseId3, id=ID_ERASE)
        self.Bind(wx.EVT_BUTTON, self.OnSaveId3, id=wx.ID_SAVE)
        self.Bind(wx.EVT_CHOICE, self.OnSelectTrack, self.track_choice)
        self.Bind(wx.EVT_BUTTON, self.OnTrackAppend, id=ID_APPEND_TRACK)
        self.Bind(wx.EVT_BUTTON, self.OnTrackInsert, id=ID_INSERT_TRACK)
        self.Bind(wx.EVT_BUTTON, self.OnTrackRemove, id=ID_REMOVE_TRACK)
        self.Bind(wx.EVT_BUTTON, self.OnSplitFile, id=ID_SPLIT_FILE)
        # end wxGlade

        self.begin_field.Bind(wx.EVT_KILL_FOCUS, self.ValidateBeginTime)
        self.end_field.Bind(wx.EVT_KILL_FOCUS, self.ValidateEndTime)
        self.track_title_field.Bind(wx.EVT_KILL_FOCUS, self.SaveTrackTitle)
        self.Bind(wx.EVT_CLOSE, self.OnClose)

        # Hello world
        wx.LogMessage("Pympa launched at %s\n-----\n" % time.strftime("%H:%M:%S"))

    def __set_properties(self):
    #-------------------------
        # begin wxGlade: MyFrame.__set_properties
        self.SetTitle("Pympa v.0.6")
        self.file_choice.SetSelection(0)
        self.reloadbtn.Enable(False)
        self.openbtn.SetDefault()
        self.track_field.SetMinSize((40, -1))
        self.title_label.SetMinSize((75, -1))
        self.artist_label.SetMinSize((75, -1))
        self.album_label.SetMinSize((75, -1))
        self.year_label.SetMinSize((75, -1))
        self.year_field.SetMinSize((60, -1))
        self.genre_field.SetSelection(0)
        self.comment_label.SetMinSize((75, -1))
        self.check_comment_adjust.SetValue(1)
        self.save_btn.SetDefault()
        self.id3_tab.Enable(False)
        self.track_choice.SetSelection(0)
        self.track_title_label.SetMinSize((78, -1))
        self.begin_label.SetMinSize((78, -1))
        self.end_label.SetMinSize((78, -1))
        self.append_btn.SetFocus()
        self.remove_btn.Enable(False)
        self.split_btn.Enable(False)
        self.split_tab.Enable(False)
        self.split_tab.Hide()
        self.logwindow.SetMinSize((-1, 75))
        # end wxGlade

        # info tab
        self.DeactivateInfo()
        # id3 tab
        self.genre_field.AppendItems(mpalib.genres)
        # logger
        log = MyLog(self.logwindow)
        wx.Log_SetActiveTarget(log)

    def __do_layout(self):
    #--------------------
        # begin wxGlade: MyFrame.__do_layout
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        split_v_sizer = wx.BoxSizer(wx.VERTICAL)
        editor_sizer = wx.StaticBoxSizer(self.editor_sizer_staticbox, wx.VERTICAL)
        split_bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        frames_lsizer = wx.BoxSizer(wx.HORIZONTAL)
        end_sizer = wx.BoxSizer(wx.HORIZONTAL)
        begin_sizer = wx.BoxSizer(wx.HORIZONTAL)
        title_sizer = wx.BoxSizer(wx.HORIZONTAL)
        track_sizer = wx.StaticBoxSizer(self.track_sizer_staticbox, wx.HORIZONTAL)
        id3_v_sizer = wx.BoxSizer(wx.VERTICAL)
        bottom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        options_sizer = wx.StaticBoxSizer(self.options_sizer_staticbox, wx.VERTICAL)
        taginfo_sizer = wx.StaticBoxSizer(self.taginfo_sizer_staticbox, wx.VERTICAL)
        row6 = wx.BoxSizer(wx.HORIZONTAL)
        row5 = wx.BoxSizer(wx.HORIZONTAL)
        row4 = wx.BoxSizer(wx.HORIZONTAL)
        row3 = wx.BoxSizer(wx.HORIZONTAL)
        row2 = wx.BoxSizer(wx.HORIZONTAL)
        row1 = wx.BoxSizer(wx.HORIZONTAL)
        info_v_sizer = wx.BoxSizer(wx.VERTICAL)
        sizer_3 = wx.BoxSizer(wx.HORIZONTAL)
        xing_sizer = wx.StaticBoxSizer(self.xing_sizer_staticbox, wx.VERTICAL)
        sizer_6 = wx.BoxSizer(wx.HORIZONTAL)
        info_sizer = wx.StaticBoxSizer(self.info_sizer_staticbox, wx.VERTICAL)
        choice_sizer = wx.StaticBoxSizer(self.choice_sizer_staticbox, wx.HORIZONTAL)
        choice_sizer.Add(self.file_choice, 1, wx.ALL|wx.ADJUST_MINSIZE, 1)
        info_v_sizer.Add(choice_sizer, 0, wx.ALL|wx.EXPAND, 3)
        info_sizer.Add(self.info, 1, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 2)
        sizer_3.Add(info_sizer, 1, wx.RIGHT|wx.EXPAND, 2)
        xing_sizer.Add(self.xing, 1, wx.ALL|wx.EXPAND|wx.ADJUST_MINSIZE, 2)
        sizer_6.Add(self.reloadbtn, 0, wx.ALL|wx.ADJUST_MINSIZE, 1)
        sizer_6.Add(self.openbtn, 0, wx.ALL|wx.ADJUST_MINSIZE, 1)
        xing_sizer.Add(sizer_6, 0, wx.EXPAND, 0)
        sizer_3.Add(xing_sizer, 1, wx.LEFT|wx.EXPAND, 2)
        info_v_sizer.Add(sizer_3, 1, wx.ALL|wx.EXPAND, 3)
        self.info_tab.SetAutoLayout(True)
        self.info_tab.SetSizer(info_v_sizer)
        info_v_sizer.Fit(self.info_tab)
        info_v_sizer.SetSizeHints(self.info_tab)
        row1.Add(self.track_label, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 5)
        row1.Add(self.track_field, 0, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        taginfo_sizer.Add(row1, 0, wx.ALL|wx.EXPAND, 2)
        row2.Add(self.title_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        row2.Add(self.title_field, 1, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        taginfo_sizer.Add(row2, 0, wx.ALL|wx.EXPAND, 2)
        row3.Add(self.artist_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        row3.Add(self.artist_field, 1, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        taginfo_sizer.Add(row3, 0, wx.ALL|wx.EXPAND, 2)
        row4.Add(self.album_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        row4.Add(self.album_field, 1, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        taginfo_sizer.Add(row4, 0, wx.ALL|wx.EXPAND, 2)
        row5.Add(self.year_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        row5.Add(self.year_field, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        row5.Add(self.genre_label, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        row5.Add(self.genre_field, 0, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        taginfo_sizer.Add(row5, 0, wx.ALL|wx.EXPAND, 2)
        row6.Add(self.comment_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        row6.Add(self.comment_field, 1, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 5)
        taginfo_sizer.Add(row6, 0, wx.ALL|wx.EXPAND, 2)
        taginfo_sizer.Add((0, 10), 1, wx.ADJUST_MINSIZE, 0)
        id3_v_sizer.Add(taginfo_sizer, 1, wx.ALL|wx.EXPAND, 3)
        options_sizer.Add(self.check_comment_adjust, 0, wx.ALL|wx.ADJUST_MINSIZE, 2)
        bottom_sizer.Add(options_sizer, 1, wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 3)
        btn_sizer.Add(self.erase_btn, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 3)
        btn_sizer.Add(self.save_btn, 0, wx.LEFT|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 3)
        bottom_sizer.Add(btn_sizer, 0, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ADJUST_MINSIZE, 3)
        id3_v_sizer.Add(bottom_sizer, 0, wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 3)
        self.id3_tab.SetAutoLayout(True)
        self.id3_tab.SetSizer(id3_v_sizer)
        id3_v_sizer.Fit(self.id3_tab)
        id3_v_sizer.SetSizeHints(self.id3_tab)
        track_sizer.Add(self.track_choice, 3, wx.ALL|wx.ADJUST_MINSIZE, 1)
        track_sizer.Add((35, 1), 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        track_sizer.Add(self.split_label_1, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 4)
        track_sizer.Add(self.tracks_number_label, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 2)
        split_v_sizer.Add(track_sizer, 0, wx.ALL|wx.EXPAND, 3)
        title_sizer.Add(self.track_title_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 3)
        title_sizer.Add(self.track_title_field, 4, wx.RIGHT|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 5)
        editor_sizer.Add(title_sizer, 0, wx.ALL|wx.EXPAND, 2)
        begin_sizer.Add(self.begin_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        begin_sizer.Add(self.begin_field, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        begin_sizer.Add(self.label_11, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 10)
        begin_sizer.Add(self.begin_frame_label, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 2)
        begin_sizer.Add((20, 10), 2, wx.ADJUST_MINSIZE, 0)
        editor_sizer.Add(begin_sizer, 0, wx.ALL|wx.EXPAND, 2)
        end_sizer.Add(self.end_label, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        end_sizer.Add(self.end_field, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        end_sizer.Add(self.label_12, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 10)
        end_sizer.Add(self.end_frame_label, 0, wx.LEFT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 2)
        end_sizer.Add((20, 10), 2, wx.ADJUST_MINSIZE, 0)
        editor_sizer.Add(end_sizer, 0, wx.ALL|wx.EXPAND, 2)
        editor_sizer.Add(self.static_line_1, 0, wx.ALL|wx.EXPAND, 5)
        frames_lsizer.Add(self.label_7, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 3)
        frames_lsizer.Add(self.frames_label, 1, wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 0)
        editor_sizer.Add(frames_lsizer, 1, wx.TOP|wx.EXPAND|wx.ALIGN_BOTTOM, 2)
        split_bottom_sizer.Add(self.label_8, 0, wx.LEFT|wx.RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 3)
        split_bottom_sizer.Add(self.time_label, 1, wx.ALIGN_CENTER_VERTICAL|wx.ADJUST_MINSIZE, 0)
        split_bottom_sizer.Add(self.append_btn, 1, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 1)
        split_bottom_sizer.Add(self.insert_btn, 1, wx.LEFT|wx.RIGHT|wx.EXPAND|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 1)
        split_bottom_sizer.Add(self.remove_btn, 1, wx.LEFT|wx.EXPAND|wx.ALIGN_BOTTOM|wx.ADJUST_MINSIZE, 1)
        editor_sizer.Add(split_bottom_sizer, 0, wx.BOTTOM|wx.EXPAND, 2)
        split_v_sizer.Add(editor_sizer, 4, wx.ALL|wx.EXPAND, 3)
        split_v_sizer.Add(self.split_btn, 1, wx.ALL|wx.EXPAND, 2)
        self.split_tab.SetAutoLayout(True)
        self.split_tab.SetSizer(split_v_sizer)
        split_v_sizer.Fit(self.split_tab)
        split_v_sizer.SetSizeHints(self.split_tab)
        self.notebook.AddPage(self.info_tab, "General")
        self.notebook.AddPage(self.id3_tab, "Id3v1.1")
        self.notebook.AddPage(self.split_tab, "Splitter")
        main_sizer.Add(self.notebook, 1, wx.EXPAND, 0)
        main_sizer.Add(self.logwindow, 0, wx.EXPAND|wx.ADJUST_MINSIZE, 0)
        self.SetAutoLayout(True)
        self.SetSizer(main_sizer)
        main_sizer.Fit(self)
        main_sizer.SetSizeHints(self)
        self.SetMinSize((473, 405))
        self.Layout()
        self.Centre()
        # end wxGlade

        #self.SetMinSize((470, 400))

    def OnOpenFile(self, event): # wxGlade: MyFrame.<event_handler>
    #--------------------------
        last_dir = os.getcwd()
        dlg = wx.FileDialog(self, message="Choose a file",
              defaultDir=os.getcwd(), defaultFile="", wildcard=wildcard,
              style=wx.OPEN|wx.MULTIPLE|wx.CHANGE_DIR)

        if dlg.ShowModal() == wx.ID_OK:
            filenames = dlg.GetFilenames()
            filenames.sort()
            opened = []
            for fname in filenames:
                try:
                    opened.append(mpalib.MpegAudioFile(fname))
                except UnicodeEncodeError:
                    wx.LogWarning("Cannot translate string using chosen encoding\n")
                except:
                    wx.LogWarning("Cannot open \"%s\"\n" % fname)

            if not opened: return

            cur_dir = os.getcwd()
            last_dir = getattr(self, "current_dir", "")
            if cur_dir != last_dir:
                wx.LogMessage("Current dir: \"%s\"\n" % os.getcwd())
                self.current_dir = cur_dir

            self.CloseOpenFiles()
            items = [(mpeg.name, mpeg) for mpeg in opened]
            self.openfiles = dict(items)
            self.file_choice.Clear()
            if len(opened) > 1:
                self.file_choice.Append(ALL)
            for fname in self.openfiles:
                self.file_choice.Append(fname)
                wx.LogMessage("Opened \"%s\"\n" % fname)

            self.file_choice.Enable()
            self.choice_sizer_staticbox.Enable()
            self.reloadbtn.Enable()
            self.id3_tab.Enable()
            self.file_choice.Select(0)
            self.ShowSelectedFile()

        dlg.Destroy()

    def OnFileSelect(self, event): # wxGlade: MyFrame.<event_handler>
    #----------------------------
        if event.GetString() != self.current_fname:
            self.ShowSelectedFile()

    def ShowSelectedFile(self):
    #-------------------------
        if not self.file_choice.GetCount():
            self.DeactivateInfo()
            self.id3_tab.Disable()
            self.DeactivateSplitter()
            return

        selected = self.file_choice.GetStringSelection()
        self.current_fname = selected

        if selected == ALL:
            tags = [set(mpeg.id3.items()) for mpeg in self.openfiles.values()]
            intersect = lambda sofar, next: sofar.intersection(next)
            common = reduce(intersect, tags)
            self.PrintInfo(*self.openfiles.values())
            self.PrintId3(dict(common))
            self.DeactivateSplitter()
        else:
            mpeg = self.current_file = self.openfiles[selected]
            self.PrintInfo(mpeg)
            self.PrintId3(mpeg.id3)
            self.InitSplitter()
            wx.LogMessage("Showing file \"%s\"\n" % selected)

    def ReloadSelectedFile(self, event): # wxGlade: MyFrame.<event_handler>
    #---------------------------
        selected = self.file_choice.GetStringSelection()

        if selected == ALL:
            self.CloseOpenFiles(clear=False)
            for fname in self.openfiles:
                try:
                    self.openfiles[fname] = mpalib.MpegAudioFile(fname)
                    wx.LogMessage("Reloaded \"%s\"\n" % fname)
                except:
                    wx.LogWarning("Cannot open \"%s\n\"" % fname)
                    self.file_choice.Delete(self.file_choice.FindString(fname))
                    del self.openfiles[fname]
        else:
            self.openfiles[selected].close()
            index = self.file_choice.GetSelection()
            try:
                self.openfiles[selected] = mpalib.MpegAudioFile(selected)
                wx.LogMessage("Reloaded \"%s\"\n" % selected)
            except:
                wx.LogWarning("Cannot open \"%s\"\n" % selected)
                self.file_choice.Delete(index)
                del self.openfiles[selected]
                self.file_choice.Select(0)

        if not self.openfiles:
            self.file_choice.Clear()

        self.ShowSelectedFile()

    def CloseOpenFiles(self, clear=True):
    #-----------------------------------
        self.__dict__.setdefault("openfiles", {})
        for mpeg in self.openfiles.values():
            mpeg.close()
        if clear: self.openfiles.clear()


    def OnEraseId3(self, event): # wxGlade: MyFrame.<event_handler>
    #--------------------------
        tag = mpalib.Id3Tag1.default
        self.WriteId3(tag)
        for field in mpalib.Id3Tag1.fields[:-1]:
            control = getattr(self, field + "_field")
            control.SetValue("")
        if self.genre_field.GetString(1) == VARIOUS:
            self.genre_field.Delete(1)
        self.genre_field.SetSelection(0)

    def OnSaveId3(self, event): # wxGlade: MyFrame.<event_handler>
    #-------------------------
        if self.ValidateCommentSize() == False:
            return
        fields = mpalib.Id3Tag1.fields[:-1]  # we leave "genre" out
        get_value = lambda f: (f, (getattr(self, f + "_field")).GetValue())
        fields = [(key, value) for (key, value) in map(get_value, fields) if value != VARIOUS]

        genre = self.genre_field.GetStringSelection()
        if genre != VARIOUS:
            value = mpalib.genres.index(genre)
            fields.append(("genre", str(value)))

        self.WriteId3(fields)

    def WriteId3(self, fields):
    #-------------------------
        if self.current_fname == ALL:
            dest_files = self.openfiles.values()
        else:
            dest_files = [self.current_file]

        for mpeg in dest_files:
            try:
                mpeg.update_id3(fields)
                wx.LogMessage("Updated \"%s\" id31.1 tag\n" % mpeg.name)
            except:
                wx.LogWarning("Cannot write Id3 info to \"%s\"\n" % mpeg.name)

    def DeactivateInfo(self):
    #-----------------------
        self.file_choice.Disable()
        self.choice_sizer_staticbox.Disable()
        self.info_sizer_staticbox.Disable()
        self.xing_sizer_staticbox.Disable()
        self.info.SetLabel("")
        self.xing.SetLabel("")
        self.reloadbtn.Disable()

    def DeactivateSplitter(self):
    #---------------------------
        self.track_choice.Clear()
        self.split_tab.Disable()
        # clear labels here
        self.tracks_number_label.SetLabel("0")
        self.track_title_field.SetValue("")
        self.begin_field.SetValue("")
        self.end_field.SetValue("")
        self.begin_frame_label.SetLabel("")
        self.end_frame_label.SetLabel("")
        self.frames_label.SetLabel("")
        self.time_label.SetLabel("")

    def InitSplitter(self):
    #---------------------
        self.track_choice.Clear()
        self.tracks = []
        self.split_tab.Enable()
        self.MakeNewTrack(0)



    def MakeNewTrack(self, position, title="Untitled"):
    #-------------------------------------------------
        track = Track()
        if self.track_choice.IsEmpty():
            position = 0
            track.begin = 0
            track.end = self.current_file.length
        else:
            try:
                old = self.tracks[position]
                track.begin = old.begin
                track.end = old.begin = old.end - (old.end - old.begin) / 2
            except:
                old = self.tracks[position - 1]
                track.end = old.end
                track.begin = old.end = old.end - (old.end - old.begin) / 2

        track.title = title
        self.tracks.insert(position, track)
        voice = "%02d - %s" % (position + 1, track.title)
        self.track_choice.Insert(voice, position)
        self.track_choice.Select(position)
        self.ShowSelectedTrack()

    def NumberTracks(self, after=0):
    #------------------------------
        first = after + 1
        for i in range(first, self.track_choice.GetCount()):
            new = ("%02d" % (i + 1)) + self.track_choice.GetString(i)[2:]
            self.track_choice.SetString(i, new)

    def ShowSelectedTrack(self):
    #--------------------------
        if self.track_choice.GetCount() == 1:
            self.split_btn.Disable()
            self.remove_btn.Disable()
        else:
            self.split_btn.Enable()
            self.remove_btn.Enable()

        track = self.tracks[self.track_choice.GetSelection()]
        self.tracks_number_label.SetLabel(str(len(self.tracks)))
        self.track_title_field.SetValue(track.title)
        self.begin_field.SetValue(mpalib.seconds_to_str(track.begin))
        self.end_field.SetValue(mpalib.seconds_to_str(track.end))
        frame = lambda s: round(s / self.current_file.frame_length)
        begin_frame = frame(track.begin)
        end_frame = frame(track.end)
        total_frames = end_frame - begin_frame
        self.begin_frame_label.SetLabel(str(begin_frame))
        self.end_frame_label.SetLabel(str(end_frame))
        self.frames_label.SetLabel(str(total_frames))
        time = mpalib.seconds_to_str(total_frames * self.current_file.frame_length)
        self.time_label.SetLabel(time)

        #wx.LogMessage("file length: %f\n" % self.current_file.length)
        #wx.LogMessage("file length: %f\n" % (total_frames * self.current_file.frame_length))


        if track.begin == 0:
            self.begin_field.Disable()
        else:
            self.begin_field.Enable()

        if track.end == self.current_file.length:
            self.end_field.Disable()
        else:
            self.end_field.Enable()

    def SaveTrackTitle(self, event): # wxGlade: MyFrame.<event_handler>
    #------------------------------
        index = self.track_choice.GetSelection()
        track = self.tracks[index]
        new_title = self.track_title_field.GetValue()
        if not new_title:
            new_title = "Untitled"
            self.track_title_field.SetValue(new_title)
        track.title = new_title
        self.track_choice.SetString(index, "%02d - %s" % (index + 1, new_title))
        self.track_choice.Select(index)

    def ValidateBeginTime(self, event): # wxGlade: MyFrame.<event_handler>
    #---------------------------------
        index = self.track_choice.GetSelection()
        track = self.tracks[index]
        prev_track = self.tracks[index - 1]
        field = self.begin_field
        try:
            time = mpalib.str_to_seconds(field.GetValue())
            if time >= track.end or time <= prev_track.begin:
                raise ValueError
            prev_track.end = track.begin = time
            self.ShowSelectedTrack()
        except:
            field.SetValue(mpalib.seconds_to_str(track.begin))

    def ValidateEndTime(self, event): # wxGlade: MyFrame.<event_handler>
    #-------------------------------
        index = self.track_choice.GetSelection()
        track = self.tracks[index]
        next_track = self.tracks[index + 1]
        field = self.end_field
        try:
            time = mpalib.str_to_seconds(field.GetValue())
            if time <= track.begin or time >= next_track.end:
                raise ValueError
            next_track.begin = track.end = time
            self.ShowSelectedTrack()
        except:
            field.SetValue(mpalib.seconds_to_str(track.end))

    def ValidateCommentSize(self):
    #----------------------------
        track = self.track_field.GetValue()
        comment = self.comment_field.GetValue()
        if  track not in ("", VARIOUS) and len(comment) > 28:
            if self.check_comment_adjust.IsChecked():
                self.comment_field.SetValue(comment[:28])
            else:
                message = """The comment you typed is too long.
You may either shorten it to 28 characters or leave the track field empty."""
                wx.MessageBox(message, "Cannot write Id3",
                wx.OK|wx.ICON_EXCLAMATION, self)
                return False
        return True

    def PrintInfo(self, *mpegs):
    #--------------------------
        if len(mpegs) == 1:
            mpeg = mpegs[0]
            self.info_sizer_staticbox.Enable()
            self.xing_sizer_staticbox.Enable()
            mpeginfo = mpeg.__str__()
            xinginfo = mpeg.xing_header.__str__()
            self.info.SetLabel(mpeginfo)
            self.xing.SetLabel(xinginfo)
        else:
            self.info_sizer_staticbox.Disable()
            self.xing_sizer_staticbox.Disable()
            self.info.SetLabel("")
            self.xing.SetLabel("")

    def PrintId3(self, id3):
    #----------------------
        #print mpalib.Id3Tag1.default_fields
        for field in mpalib.Id3Tag1.fields:
            control = getattr(self, field + "_field")
            if field == "genre":
                if control.GetString(1) == VARIOUS:
                    control.Delete(1)
                try:
                    index = int(id3[field] or "255")
                    if index in range(len(mpalib.genres)):
                        genre = mpalib.genres[index]
                    else:
                        genre = ""
                    control.SetStringSelection(genre)
                except:
                    control.SetSelection(control.Append(VARIOUS))
            else:
                control.SetLabel(id3.get(field, VARIOUS))

    def OnShowAbout(self, event): # wxGlade: MyFrame.<event_handler>
    #---------------------------
        import  wx.lib.dialogs
        message = '''
 PYMPA v0.6b
 -----------------------------------------------------------------

  Author :: Marco Rimoldi <rimarko@libero.it>
 License :: Gnu GPL (see the included COPYING file)
     Web :: http://pympa.sourceforge.net

 MANY THANKS TO:
 - Guido
 - Konrad Windszus
 - the wxPython developers
 - the wxGlade developers

 ...and to YOU for using Pympa!

 -----------------------------------------------------------------

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful, but
 WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Pympa; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA'''

        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, message, "About")
        dlg.ShowModal()

    def OnSplitFile(self, event): # wxGlade: MyFrame.<event_handler>
    #---------------------------

        dlg = wx.DirDialog(self, "Choose the destination directory:", defaultPath=os.getcwd(),
                          style=wx.DD_DEFAULT_STYLE|wx.DD_NEW_DIR_BUTTON)

        if dlg.ShowModal() == wx.ID_OK:
            dest = dlg.GetPath()
            dlg.Destroy()
        else:
            dlg.Destroy()
            return

        cutpoints = []
        titles = []
        for track in self.tracks:
            cutpoints.append(track.end)
            titles.append(track.title)
        cutpoints.pop() # get rid of the last value
        self.current_file.split(cutpoints, titles, dest)
        wx.LogMessage("Splitting complete: %d files written to '%s'\n" % (len(titles), dest))


    def OnSelectTrack(self, event): # wxGlade: MyFrame.<event_handler>
    #-----------------------------
        self.ShowSelectedTrack()

    def OnTrackAppend(self, event): # wxGlade: MyFrame.<event_handler>
    #-----------------------------
        pos = self.track_choice.GetCount()
        self.MakeNewTrack(pos)

    def OnTrackInsert(self, event): # wxGlade: MyFrame.<event_handler>
    #-----------------------------
        pos = self.track_choice.GetSelection()
        self.MakeNewTrack(pos)
        self.NumberTracks(after=pos)

    def OnTrackRemove(self, event): # wxGlade: MyFrame.<event_handler>
    #-----------------------------
        index = self.track_choice.GetSelection()
        track = self.tracks[index]
        self.tracks.remove(track)
        self.track_choice.Delete(index)
        try:
            self.tracks[index].begin = track.begin
            self.NumberTracks(after=index - 1)
            self.track_choice.Select(index)
        except:
            self.tracks[index - 1].end = track.end
            self.track_choice.Select(index - 1)
        self.ShowSelectedTrack()


    def OnMenuExit(self, event): # wxGlade: MyFrame.<event_handler>
    #--------------------------
        self.Close()

    def OnClose(self, event): # wxGlade: MyFrame.<event_handler>
    #-----------------------
        self.CloseOpenFiles()
        self.Destroy()

# end of class MyFrame


class MyApp(wx.App):

    def OnInit(self):
    #---------------
        wx.InitAllImageHandlers()
        main_frame = MyFrame(None, -1, "")
        self.SetTopWindow(main_frame)
        main_frame.Show()
        return 1

# end of class MyApp

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
    Pympa = MyApp(0)
    Pympa.MainLoop()
