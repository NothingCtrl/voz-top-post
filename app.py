#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import requests
import os
import csv
import json
import hashlib
import time
import datetime
from pyquery import PyQuery
import re

def strip_vietnamese(string):
    s1 = u'ÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚÝàáâãèéêìíòóôõùúýĂăĐđĨĩŨũƠơƯưẠạẢảẤấẦầẨẩẪẫẬậẮắẰằẲẳẴẵẶặẸẹẺẻẼẽẾếỀềỂểỄễỆệỈỉỊịỌọỎỏỐốỒồỔổỖỗỘộỚớỜờỞởỠỡỢợỤụỦủỨứỪừỬửỮữỰựỲỳỴỵỶỷỸỹ'
    s0 = u'AAAAEEEIIOOOOUUYaaaaeeeiioooouuyAaDdIiUuOoUuAaAaAaAaAaAaAaAaAaAaAaAaEeEeEeEeEeEeEeEeIiIiOoOoOoOoOoOoOoOoOoOoOoOoUuUuUuUuUuUuUuYyYyYyYy'

    def remove_accents(input_str):
        s = ''
        print
        input_str.encode('utf-8')
        for c in input_str:
            if c in s1:
                s += s0[s1.index(c)]
            else:
                s += c
        return s
    return remove_accents(string)


class Voz:
    base_url = 'https://forums.voz.vn'
    headers = {}
    session = None
    dir_path = None
    top_hit_threads = []

    def _read_header_file(self):
        # open 'browser_data.json' for header data (browser, cookie...)
        # this file should be in the same root folder with app.py
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if not self.dir_path:
            self.dir_path = dir_path
        browser_data_file = self.dir_path + '/browser_data.json'
        if os.path.isfile(browser_data_file):
            with open(browser_data_file) as f:
                return json.load(f)
        else:
            return {}

    def _read_cookie(self):
        dir_path = os.path.dirname(os.path.realpath(__file__))
        if not self.dir_path:
            self.dir_path = dir_path
        cookie_file = self.dir_path + '/cookie.json'
        if os.path.isfile(cookie_file):
            with open(cookie_file) as f:
                return json.load(f)['cookie']
        else:
            return {}

    def _login_session(self):
        if not self.session:
            self.session = requests.session()
            cookie = self._read_cookie()
            cookie = requests.utils.cookiejar_from_dict(dict(p.split('=') for p in cookie.split('; ')))
            self.set_header(self._read_header_file())
            self.session.cookies = cookie

    def set_header(self, headers):
        self.headers = headers

    def get_request(self, url, data):
        self._login_session()
        return self.session.get(url, data=data, headers=self.headers)

    def _get_posts_in_page(self, pq_threadlist, first_post_inline=False):
        """
        :param pq_threadlist: PqQuery object of selector (table#threadslist > tr)
        :return:
        """
        result = []
        for tr in pq_threadlist.items():
            i = 0
            col1_icon = col2_sp = col3_title = col4_lastp = col5_rep = col6_views = col7_forum = None
            for td in tr('td').items():
                i += 1
                if i == 1:
                    col1_icon = td('.alt1')
                if i == 2:
                    col2_sp = td('.alt2')
                if i == 3:
                    col3_title = td('.alt1')
                if i == 4:
                    col4_lastp = td('.alt2')
                if i == 5:
                    col5_rep = td('.alt1')
                if i == 6:
                    col6_views = td('.alt2')
                if i == 7:
                    col7_forum = td('.alt1')
                if col1_icon and col2_sp and col3_title and col4_lastp and col5_rep and col6_views and col7_forum:
                    title = None
                    thread_url = None
                    last_page_url = None
                    author = PyQuery(col3_title.html())('div.smallfont').text().strip()
                    for a in PyQuery(col3_title.html())('a'):
                        if not thread_url:
                            thread_url = a.attrib.get('href')
                        if 'prefixid' in thread_url or '=newpost' in thread_url:
                            thread_url = None
                        if thread_url and not title:
                            title = a.text
                        if a.text == 'Last Page':
                            last_page_url = a.attrib.get('href')
                            break
                        elif 'showthread.php?t=' in a.attrib.get('href'):
                            last_page_url = a.attrib.get('href')

                    if title and thread_url and len(title.strip()) > 0:
                        result.append({
                            'title': title,
                            'url': "{}/{}".format(self.base_url, thread_url),
                            'id': int(thread_url.split('?')[1].split('=')[1]),
                            'replies': int(col5_rep.text().replace(',', '')),
                            'views': int(col6_views.text().replace(',', '')),
                            'forum': col7_forum.text(),
                            'forum_id': int(PyQuery(col7_forum.html())('a')[0].attrib.get('href').split('?')[1].split('=')[1]),
                            'first_post': first_post_inline and self.get_thread_first_post(int(thread_url.split('=')[1])) or None,
                            'last_page_url': last_page_url and "{}/{}".format(self.base_url, last_page_url) or None,
                            'author': author
                        })
                        if first_post_inline:
                            time.sleep(1)
        return result

    def _threads_to_html(self, threads, page_title=None):
        date_create = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M")
        total = len(threads)
        count = 0
        text = ''
        for th in threads:
            count += 1
            if 'first_post' in th and th['first_post']:
                first_post = th['first_post']
            else:
                first_post = self.get_thread_first_post(int(th['url'].split('=')[1]), strip_html=False)
                print("  -> Process {}".format(strip_vietnamese(th['title']).encode('utf-8')))
                time.sleep(1)
            hit_count = ''
            if 'hit_count' in th:
                hit_count = "<td>Hit: {}</td>".format(th['hit_count'])
            last_page = ''
            if 'last_page_url' in th and th['last_page_url']:
                last_page = " <a href='{}#{}' target='_blank'>[Last Page]</a>".format(th['last_page_url'], date_create)
            text += u'<tr id={}>' \
                    '<td style="width: 70%;"><a href="{}#{}" target=\'_blank\'>[{}/{}] {}</a> <a href="#{}_{}" onclick="toggle_visibility(\'first-{}\')"><strong>[Show/Hide]</strong></a>{} (author: {}) <span onclick="deleteRow(\'{}\')" style="font-size: 9px; cursor: pointer; color: gray">delete</span><div id="first-{}" style="background: #efefef; display: none" class="toggle-content"><br>{}</div></td>' \
                    '<td>Views: {:,}</td>' \
                    '<td>Replies: {:,}</td>' \
                    '<td>Forum: {}</td>' \
                    '{}</tr>'.format(th['id'], th['url'], date_create, count, total, th['title'], th['id'], date_create, th['id'], last_page, th['author'], th['id'], th['id'], first_post, th['views'], th['replies'], th['forum'], hit_count)
        html = u"""<html><head><meta charset="UTF-8"><title>VOZ | %s</title> 
        <!-- Suppress browser request for favicon.ico -->
        <link rel="shortcut icon"type="image/x-icon" href="data:image/x-icon;,">
        <style type="text/css">table {border-collapse: collapse;} table, th, td {border: 1px solid #a1a1a1; font-family: Arial,serif; font-size: 14px;} td {height: 32px;} a {text-decoration: none;} body {background: #e0dbdb}
        tbody tr:nth-child(odd){ background-color: #cecece;}
        tr:hover {background-color: #ffffff !important;} 
        </style>
        <script src="https://code.jquery.com/jquery-3.3.1.min.js" integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8=" crossorigin="anonymous"></script> 
        </head><body><div style="font-family: Arial,serif; font-size: 14px; padding-bottom: 10px"><a href="../">Home</a> | <input type="checkbox" name="auto_toggle" value="1" id="auto_toggle"> Auto toggle content | <input type="checkbox" name="hide_deleted" value="1" id="hide_deleted"> Hide deleted thread(s) (<span style="cursor: pointer;" onclick="clearDeletedThread()">clear list</span>)</div><table style="width: 98%%"><tbody>%s</tbody></table>
<script type="text/javascript">
    var favIcon = "iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAAABGdBTUEAALGPC/xhBQAAACBjSFJNAAB6JgAAgIQAAPoAAACA6AAAdTAAAOpgAAA6mAAAF3CculE8AAAATlBMVEUAAAAkRXkiSXsiSXsjSXwjSH0jSXwjSXwjSXwiSXwjSXwiSXwlS3UbTWUjSH0jSXwiSX0iSHwjSXwiSXslRX4jSXwjSXwiSXojSXwAAAB5V3sJAAAAGHRSTlMAElp0mbHX8r2kik4JA0P4ZDfgfhroyigwxk/FAAAAAWJLR0QAiAUdSAAAAAd0SU1FB+MCGAA3AVRpfz4AAAHTSURBVEjHlZbbtqsgDEXBCgiIYmnV///S03IpSUD3OLypuayZRCNj9PDhMQqplJy0sTP747hFryc4q/D8zn57ns1R4S7NK3Rc3t7dibJT67K/bkEO826SbNTIoqxzoB7rgO0XcsM1OU5ksKlzwhFM47ACVcc33oHL1SlWJd+/1wan6NWqcA4pAC62jU2TyMPnkjw7VBn7QKPyTj0vJSTYIeuEzQ8xgSqXHewYszZf8SL27GALoPMQlUJTiQh7L5VPJgIqarCfUOeeujcDRTUcxB7zhU8mlqExI9jfiqqsMysxbIQOI04hQLeyocYjoDD2AnVuuVnd5pcTsdOUulRYyRRyINiPqjPPuyIOBJuvpb2+iCaSKLbOOpcygpLOfQ9bsuOnYwKT0cWOAmydV928vD1scAwajbNWEWGDY9lM7nSxf+czfEwQB4K9oYcCVPgC2zfPOGkdxl6Q4thD1nxH4ScORwtp0ul3tGJzPAflHaYUa9lSjoxBoXP7BTaZgt+nkr2IKAneaSAIrKGNdC9iD0QoGgHyUHeCkBU04PXM084Ad4j9JyAyeNCCNkvxQw5rJXFB+2vX+XYTpvCXi30OqjW//3XgXvzXz0lMY42ern9//gFSuXGcmVXZKwAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxOS0wMi0yNFQwNjo1NTowMS0wNjowMMJ1yBAAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMTktMDItMjRUMDY6NTU6MDEtMDY6MDCzKHCsAAAAAElFTkSuQmCC";    
    var docHead = document.getElementsByTagName('head')[0];       
    var newLink = document.createElement('link');
    newLink.rel = 'shortcut icon';
    newLink.href = 'data:image/png;base64,'+favIcon;
    docHead.appendChild(newLink);    
    function toggle_visibility(id) {
    	var e = document.getElementById(id);
    	if (e.style.display == 'block') {
       		e.style.display = 'none';
    	} else {
			e.style.display = 'block';
			var toggle_class = document.getElementsByClassName('toggle-content');
			var toggle_option = document.getElementById('auto_toggle');
            if (toggle_option.checked) {
                for (var i = 0; i < toggle_class.length; i++) {
                    if (id != toggle_class.item(i).id) {
                        toggle_class.item(i).style.display = 'none';
                    }
                }			
                e.scrollIntoView();
            }
    	}
	}
	
	function deleteRow(id) {
	    $('#' + id).hide();
	    saveDeleteThread(id);
	}
	
	// Retrieve your data from locaStorage
    var saveData = JSON.parse(localStorage.saveData || null) || {};
    console.log(saveData);
    
    // Store your data.
    function saveDeleteThread(thread_id) {
        var deletedThreads = loadDeletedThreads();
        if (!deletedThreads.includes(thread_id)) {
            deletedThreads.push(thread_id);
			saveData.deleteThread = deletedThreads;
			localStorage.saveData = JSON.stringify(saveData);
			console.log("Add id: " + thread_id + " to deleted thread list")
		}
    }
    
    // load deleted thread
    function loadDeletedThreads() {
        return saveData.deleteThread || [];       
    }
    
    $('#hide_deleted').change(function () {
		if ($('#hide_deleted').is(':checked')) {
		    for (var i = 0; i < saveData.deleteThread.length; i++) {
		        $('#' + saveData.deleteThread[i]).hide();
			}
		} else {
		    for (var i = 0; i < saveData.deleteThread.length; i++) {
		        $('#' + saveData.deleteThread[i]).show();
			}
		}
    });
    
    function clearDeletedThread() {
        saveData.deleteThread = [];
        localStorage.saveData = JSON.stringify(saveData);
        alert('Cleared!')
    }
	
</script></body></html>""" % (date_create, text)
        if os.name == 'nt':
            store_dir = "{}\\voz".format(self.dir_path)
            if not page_title:
                file = "{}\\voz_new_post_top_{}.html".format(store_dir, date_create)
            else:
                file = "{}\\{}.html".format(store_dir, page_title)
        else:
            store_dir = "{}/voz".format(self.dir_path)
            if not page_title:
                file = "{}/voz_new_post_top_{}.html".format(store_dir, date_create)
            else:
                file = "{}/{}.html".format(store_dir, page_title)

        if not os.path.isdir(store_dir):
            os.mkdir(store_dir)

        if not os.path.isfile(file):
            with open(file, 'wb') as writer:
                writer.write(html.encode("UTF-8"))
            writer.close()
            time.sleep(1)
            return file

    def _update_day_top_hit(self, threads):
        if not self.top_hit_threads:
            for th in threads:
                th['hit_count'] = 1
                self.top_hit_threads.append(th)
        else:
            for th in threads:
                h_index = 0
                match = False
                for h in self.top_hit_threads:
                    if th['id'] == h['id']:
                        match = True
                        self.top_hit_threads[h_index]['hit_count'] += 1
                        break
                if not match:
                    th['hit_count'] = 1
                    self.top_hit_threads.append(th)


    def get_thread_first_post(self, thread_id, strip_html=True):
        url = "https://forums.voz.vn/showthread.php?t={}".format(thread_id)
        rs = self.get_request(url, {})
        if rs.status_code == 200:
            pq = PyQuery(rs.text)
            trs = pq('table.tborder.voz-postbit.neo_postbit > tr')
            index = 0
            for tr in trs.items():
                index += 1
                if index == 3:
                    if not strip_html:
                        div_content = PyQuery(tr.html())('div.voz-post-message')
                        html = div_content.html().replace('<img src=', '<img style="max-width: 850;" src=')
                        html = html.replace('src="/images/', 'src="{}/images/'.format(self.base_url))
                        html = html.replace('src="images/', 'src="{}/images/'.format(self.base_url))
                        return html.replace('/redirect/index.php?link=', '{}/redirect/index.php?link='.format(self.base_url))
                    else:
                        text = re.sub('<[^<]+?>', '', tr.text()).replace('"', '')
                        return re.sub(r'\n\s*\n', '\n\n', text)
        return None


    def get_new_post(self, open_result_page=True, limit_pages=40, filter_top=True,
                     ignore_forums=(11, 12, 68, 72, 76, 80, 233, 237, 241, 245, 249, 253, 254, 281)):
        """
        :param open_result_page:
        :param limit_pages: maximum number page to fetch thread
        :param filter_top:
        :param ignore_forums:
             11:    Games               / Thao luan chung
             12:    Games               / MMO -- Game Online
             68:    Khu thuong mai      / May tinh de ban
             72:    Khu thuong mai      / Máy tính xách tay
             76:    Khu thuong mai      / Điện thoại di động
             80:    Khu thuong mai      / Các sản phẩm, dịch vụ khác
             233:   Games               / Pokemon GO
             237:   Games               / Overwatch
             241:   Games               / Hearthstone
             245:   Games               / Dota2
             249:   Games               / FPS
             253:   Games               / League of Legends
             254:   Games               / Garena - Liên Quân Mobile
             281:   Games               / Crossfire Legends
        :return:
        """
        # new post:             https://forums.voz.vn/search.php?do=getnew
        # a page in new post:   https://forums.voz.vn/search.php?searchid=514866229&pp=20&page=2
        url_new_post = '{}/search.php'.format(self.base_url)
        rs = self.get_request('{}?do=getnew'.format(url_new_post), {})
        if rs.status_code == 200:
            pq = PyQuery(rs.text)
            pages_link = pq('div.pagenav > table > tr > td > a')
            search_id = None
            last_page = None
            for el in pages_link:
                if not search_id and el.attrib.get('href') and len(el.attrib.get('href').split('&')) > 0:
                    search_id = el.attrib.get('href').split('?')[1].split('&')[0].split('=')[1]
                if el.attrib.get('href') and len(el.attrib.get('href').split('&')) > 0:
                    page = int(el.attrib.get('href').split('&')[-1].split('=')[1])
                    if not last_page or page > last_page:
                        last_page = page
            print("Search ID is: {}".format(search_id))
            print("Total pages is: {}".format(last_page))
            if limit_pages < last_page:
                print("  -> Limit max page = {}".format(limit_pages))
            result = []
            tr_of_first_page = pq('table#threadslist > tr')
            result += self._get_posts_in_page(tr_of_first_page)
            print("  -> Get page 1 done")
            # get post of page 2 - last page:
            if limit_pages >= 2:
                for i in range(2, limit_pages < last_page and (limit_pages + 1) or (last_page + 1)):
                    time.sleep(3)
                    url = "{}/search.php?searchid={}&&pp=20&page={}".format(self.base_url, search_id, i)
                    page_rs = self.get_request(url, {})
                    if page_rs.status_code == 200:
                        page_rs_pq = PyQuery(page_rs.text)
                        result += self._get_posts_in_page(page_rs_pq('table#threadslist > tr'))
                        print("  -> Get page {} done".format(i))
                    else:
                        print("Server error with status code {}".format(page_rs.status_code))
            if result:
                self._update_day_top_hit(result)
                total_thread = len(result)
                top_threads = []
                if filter_top:
                    print("Filter top threads in {} threads".format(total_thread))
                    for thread in result:
                        if ((thread['replies'] > 3 and thread['views'] > 0 and thread['replies'] / thread['views'] > 0.05) or
                            (thread['replies'] > 15 or thread['views'] > 500)) \
                                and thread['forum_id'] not in ignore_forums:
                            top_threads.append(thread)
                else:
                    top_threads = result
                if top_threads:
                    print("Total thread after filter: {}".format(len(top_threads)))
                    file_path = self._threads_to_html(threads=top_threads)
                    print("File report created")
                    if open_result_page:
                        if os.name == 'nt':
                            os.system("start " + file_path)  # work on Windows env
                        else:
                            os.system("open " + file_path)
        else:
            if rs.status_code == 499:
                print("Server timeout!")

    def get_day_top_hit(self, max_thread=100, reset_top_hit=True):
        if self.top_hit_threads:
            new_list = sorted(self.top_hit_threads, key=lambda k: k['hit_count'])
            if reset_top_hit:
                self.top_hit_threads = []
            top_hit_threads = []
            if len(new_list) > max_thread:
                for i in range(-max_thread, 0):
                    top_hit_threads.append(new_list[i])
            else:
                top_hit_threads = new_list
            file = self._threads_to_html(threads=top_hit_threads, page_title='voz_top_hit_day_{}'.format(datetime.datetime.now().strftime("%Y-%m-%d")))
            print("Top hit in day created {}".format(file))


if __name__ == '__main__':
    # voz = Voz()
    # voz.get_new_post(open_result_page=False)
    while 1:
        voz = Voz()
        now = datetime.datetime.now()
        if not now.minute % 45:     # check every 45 min
            voz.get_new_post(open_result_page=False)
        if now.hour == 23 and now.minute == 55:
            voz.get_day_top_hit()
        time.sleep(30)
