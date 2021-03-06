import os
import os.path
import sys
import curses
import time
# treeview for ncurses
# subclass as shown below in the fileTreeview impl.


class treeview(object):
    space = " "*200
# uncomment the below open statement and comment the below return statement to enable logging again
# log=open("/tmp/tree","wb")

    def l(self, *a):
        return
#  [self.log.write(str(i)+"\n") for i in a]
#  self.log.flush()

    def __init__(self, nodes):
        self.screen = None
        self.list = []
        self.nodes = nodes
        self.paths = []
        self.levels = {}
        self.states = {}
        self.curIndex = 0
        self.cur = self.nodes[0]
        self.level = 0
        [self.list.insert(0, i) for i in self.nodes[::-1]]
        [self.states.__setitem__(i, 0) for i in self.nodes]
        [self.levels.__setitem__(i, 0) for i in self.list]
        self.l("cur:", self.cur)

    def down(self):
        self.l("down:", "curIndex:", self.curIndex)
        if self.curIndex+1 >= len(self.list):
            return 1
        self.curIndex += 1
        self.cur = self.list[self.curIndex]
        self.level = self.levels[self.cur]
        self.show()
#  self.screen.move(self.screen.getyx()[0]+1,0)

    def up(self, show=1):
        self.l("up:", "curIndex:", self.curIndex)
        if self.curIndex <= 0:
            return 1
        self.curIndex -= 1
        self.cur = self.list[self.curIndex]
        self.level = self.levels[self.cur]
        if show == 1:
            self.show()
        return 0

    def markCollapsed(self, root):
        i = self.list.index(root)+1
        level = self.levels[root]+1
        while i < len(self.list):
            self.l("markCollapsed:", "i:", i, "listI:",
                   self.list[i], "level:", self.levels[self.list[i]])
            if self.levels.get(self.list[i], level) < level:
                break
            if self.states[self.list[i]] == 1:
                self.collapseFunc(self.list[i])
            self.states[self.list[i]] = 0
            i += 1
        return i

    def collapse(self, i=None):
        i = self.cur if i == None else i
        self.l("collapse:", "cur:", i, "canCollapse:",
               self.canCollapse(i), "state:", self.states[i])
        if self.canCollapse(i) and self.states.get(i, 1) == 1:
            newIndex = self.markCollapsed(i)
            startIndex = self.list.index(i)+1
            rem = [self.list.pop(startIndex)
                   for j in xrange(startIndex, newIndex)]
            rem.insert(0, i)
#   self.collapseFunc(rem)
            self.states[i] = 0
            self.l("collapsed:"+str(i)+" list:"+str(self.list))
        else:
            level = self.levels[self.cur]
            while self.states[self.cur] == 0 or self.levels[self.cur] >= level:
                ret = self.up(show=0)
                if ret == 1:
                    break
        self.show()

    def expand(self):
        self.l("expand:", "curIndex:", self.curIndex, "cur:", self.cur,
               "canExpand:", self.canExpand(self.cur), "state:", self.states[self.cur])
        if self.canExpand(self.cur) and self.states.get(self.cur, 0) == 0:
            new = self.expandFunc(self.cur)
            self.states[self.cur] = 1
            [self.list.insert(self.curIndex+1, i) for i in new[::-1]]
            [self.states.__setitem__(i, 0) for i in new]
            [self.levels.__setitem__(i, self.level+1) for i in new]
            self.show()

    def canReturn(self, i):
        return 1

    def getReturnable(self, i):
        return str(i)

    def show(self):
        where = self.curIndex
        half = self.maxy/2
        if half % 2 == 0:
            half -= 1
        start = 0 if self.curIndex < half else self.curIndex-half
        end = start+self.maxy
#  self.screen.addstr(0,0,str(self.list)[:self.maxx])
        line = 1
        mt = 1
        for i in xrange(start, min(len(self.list), end)):
            item = self.list[i]
            txt = item[0]
            lvl = self.levels[item]
            txt = " "*lvl+txt[:self.maxx-lvl]
            self.screen.move(line, 0)
            self.screen.clrtoeol()
            self.screen.chgat(line, 0, -1, curses.A_NORMAL)
            self.screen.addstr(line, 0, txt)
            if i == self.curIndex:
                mt = line
            line += 1
        while line < self.maxy:
            self.screen.move(line, 0)
            self.screen.chgat(line, 0, -1, curses.A_NORMAL)
            self.screen.clrtoeol()
            line += 1
        self.screen.move(mt, 0)
        self.screen.chgat(mt, 0, -1, curses.A_REVERSE)
        self.screen.touchwin()
        self.screen.refresh()

    def collapseEntireList(self):
        t = 0
        while sum(self.states.values()) > 0:
            self.collapse([i for i in self.list[::-1]
                           if self.states[i] == 1][0])
            t += 1
        return t

    def __call__(self, screen):
        self.screen = screen
        self.screen.nodelay(1)
        self.screen.keypad(1)
        curses.raw(1)
        curses.noecho()
        self.maxy, self.maxx = self.screen.getmaxyx()
        self.screen.addstr(self.maxy-1, 0, "-"*(self.maxx-2))
        self.maxy -= 2
        self.maxx -= 1
        self.show()
        while 1:
            time.sleep(0.001)
            k = self.screen.getch()
# we're using nodelay, so -1 means no keystroke.
            if k == -1:
                continue
# each time a key is pressed, it should be shown here.
# write spaces to top line of window for clear line
            if k == ord('q'):
                return None
            if k == curses.KEY_LEFT:
                self.collapse()
            if k == curses.KEY_RIGHT:
                self.expand()
            if k == curses.KEY_UP:
                self.up()
            if k == curses.KEY_DOWN:
                self.down()
            if k in (curses.KEY_ENTER, 10):
                if self.canReturn(self.cur):
                    self.collapseEntireList()
                    return self.getReturnable(self.cur)
            continue


class fileTreeview(treeview):
    def canExpand(self, i):
        return os.path.isdir(i[1])

    def canCollapse(self, x):
        return os.path.isdir(x[1])
# self.canCollapse(x)

    def expandFunc(self, x):
        return [(i.rsplit("/", 1)[-1]+"/" if self.canExpand(('', i)) else i.rsplit("/", 1)[-1], x[1].rstrip("/")+"/"+i) for i in os.listdir(x[1])]

    def collapseFunc(self, i):
        return


class nodeTreeview(treeview):
    def getReturnable(self, i):
        j = i[1]
        return j.nodeName if j.nodeName else str(j)

    def canExpand(self, x):
        return 1 if dir(x[1]) else 0

    def canCollapse(self, x):
        return self.canExpand(x)

    def expandFunc(self, x):
        ret = []
        obj = x[1]
        for i in dir(obj):
            try:
                ret.append(
                    ("%s=%s" % (i, str(getattr(obj, i, "null")),), getattr(obj, i)))
            except:
                ret.append(("%s=error" % (i,)))
        ret.sort()
        return ret

    def collapseFunc(self, x):
        pass


class bookmarkTree(treeview):
    def __init__(self, *a, **kw):
        self.js = kw.pop('js')
        treeview.__init__(self, *a, **kw)

    def canExpand(self, x):
        i = x[1]
        return i.type in [i.RESULT_TYPE_DYNAMIC_CONTAINER, i.RESULT_TYPE_QUERY, i.RESULT_TYPE_FOLDER, i.RESULT_TYPE_FOLDER_SHORTCUT]

    def canCollapse(self, i):
        return self.canExpand(i)

    def expandFunc(self, x):
        i = x[1]
        _i = i
        i = self.getSpecificType(_i)
        ret = []
        if i.containerOpen != None:
            i.containerOpen = 1
#  title,uri=i.title,i.uri
            if i.hasChildren:
                children = [i.getChild(j) for j in xrange(i.childCount)]
                [ret.append((j.title if j.title != None else '', j))
                 for j in children]
        return ret

    types = None

    def getSpecificType(self, i):
        if self.types == None:
            self.types = {
                i.RESULT_TYPE_URI: self.js.Ci.nsINavHistoryResultNode,
                i.RESULT_TYPE_VISIT: self.js.Ci.nsINavHistoryVisitResultNode,
                i.RESULT_TYPE_FULL_VISIT: self.js.Ci.nsINavHistoryFullVisitResultNode,
                i.RESULT_TYPE_DYNAMIC_CONTAINER: self.js.Ci.nsINavHistoryContainerResultNode,
                i.RESULT_TYPE_QUERY: self.js.Ci.nsINavHistoryQueryResultNode,
                i.RESULT_TYPE_FOLDER: self.js.Ci.nsINavHistoryQueryResultNode,
                i.RESULT_TYPE_SEPARATOR: self.js.Ci.nsINavHistoryResultNode,
                i.RESULT_TYPE_FOLDER_SHORTCUT: self.js.Ci.nsINavHistoryQueryResultNode
            }
        try:
            return i.QueryInterface(self.types[i.type])
        except:
            return i

    def collapseFunc(self, i):
        i[1].containerOpen = 0

    def canReturn(self, i):
        return 1 if not self.canExpand(i) else 0

    def getReturnable(self, i):
        return str(i[1].uri)


if __name__ == '__main__':
    # text,obj
    import curses
    t = fileTreeview([("/", "/")])
    curses.wrapper(t)
