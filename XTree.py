# Copyright (c) 2001 - 2005
#     Yuan Wang. All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright 
# notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the 
# documentation and/or other materials provided with the distribution.
# 3. Redistributions in any form must be accompanied by information on
# how to obtain complete source code for the X-Diff software and any
# accompanying software that uses the X-Diff software.  The source code
# must either be included in the distribution or be available for no
# more than the cost of distribution plus a nominal fee, and must be
# freely redistributable under reasonable conditions.  For an executable
# file, complete source code means the source code for all modules it
# contains.  It does not include source code for modules or files that
# typically accompany the major components of the operating system on
# which the executable file runs.
# 
# THIS SOFTWARE IS PROVIDED BY YUAN WANG "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT,
# ARE DISCLAIMED.  IN NO EVENT SHALL YUAN WANG BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

MATCH = 0
CHANGE = 1
NO_MATCH = -1
INSERT = -1
DELETE = -1
NULL_NODE = -1
NO_CONNECTION = 1048576

_TOP_LEVEL_CAPACITY = 16384
_BOT_LEVEL_CAPACITY = 4096


# <code>XTree</code> provides a DOM-like interface but somehow simplified
# Ideally, it can be replaced by any other DOM parser output tree structures.
class XTree:
#    private     _topCap, _botCap
#    private     _elementIndex, _tagIndex, self._valueCount
#    private        self._firstChild[][], self._nextSibling[][]
#    private     self._childrenCount[][], _valueIndex[][]
#    private boolean        self._isAttribute[][]
#    private     self._matching[][]
#    private long        self._hashValue[][]
#    private String        _value[][]
#    private Hashtable    self._tagNames, _cdataTable
    _root = 0
    _firstChild = []
    _nextSibling = []
    _isAttribute = []
    _valueIndex = []
    _matching = []
    _childrenCount = []
    _hashValue = []
    _value = []
    
    _value.append([])
    _tagNames = []
    
    # This hashtable is used to record CDATA section info.
    # The key is the text node id, the value is the list of 
    # (start,end) position pair of each CDATA section.
    _cdataTable = {}
    
    _elementIndex = -1
    _tagIndex = -1
    _valueCount = 0



    def __init__(self, topcap=None, botcap=None):
        self._topCap = _TOP_LEVEL_CAPACITY
        self._botCap = _BOT_LEVEL_CAPACITY
        if topcap:
            self._topCap = topcap
        if botcap:
            self._botCap = botcap
        self._initialize()

    # Initialization.
    def _initialize(self):
        self._root = 0
        self._firstChild = []
        self._nextSibling = []
        self._isAttribute = []
        self._valueIndex = []
        self._matching = []
        self._childrenCount = []
        self._hashValue = []
        self._value = []

        self._value.append([])
        self._tagNames = []

        # This hashtable is used to record CDATA section info.
        # The key is the text node id, the value is the list of 
        # (start,end) position pair of each CDATA section.
        self._cdataTable = {}

        self._elementIndex = -1
        self._tagIndex = -1
        self._valueCount = self._botCap - 1

    # ID Expansion
    def _expand(self, topid):
        self._firstChild[topid] = []
        self._nextSibling[topid] = []
        self._childrenCount[topid] = []
        self._matching[topid] = []
        self._valueIndex[topid] = []
        self._hashValue[topid] = []
        self._isAttribute[topid] = []

        for i in range(self._botCap):
            self._firstChild[topid][i] = NULL_NODE
            self._nextSibling[topid][i] = NULL_NODE
            self._childrenCount[topid][i] = 0
            self._matching[topid][i] = MATCH
            self._valueIndex[topid][i] = -1
            self._isAttribute[topid][i] = False

    # Start  -- methods for constructing a tree.
    # Add a new element to the tree.
    # @param    pid        parent id
    # @param    lsid        left-side sibling id
    # @param    tagName        element name
    # @return    the element id in the tree.
    def addElement(self, pid, lsid, tagName):
        self._elementIndex += 1

        topid = self._elementIndex / self._botCap
        botid = self._elementIndex % self._botCap
        if (botid == 0):
            self._expand(topid)

        # Check if we've already had the tag
        tagID = self._tagNames[tagName]
        if (tagID != None):
            self._valueIndex[topid][botid] = tagID.intValue()
        else:
            self._tagIndex += 1
            tagID = int(self._tagIndex)
            self._value[0][self._tagIndex] = tagName
            self._tagNames.append(tagName, tagID)
            self._valueIndex[topid][botid] = self._tagIndex

        if (pid == NULL_NODE):
            return self._elementIndex

        ptopid = pid / self._botCap
        pbotid = pid % self._botCap
        # parent-child relation or sibling-sibling relation
        if (lsid == NULL_NODE):
            self._firstChild[ptopid][pbotid] = self._elementIndex
        else:
            self._nextSibling[lsid / self._botCap][lsid % self._botCap] = self._elementIndex

        # update children count
        self._childrenCount[ptopid][pbotid] += 1

        return self._elementIndex

    # Add a text node.
    # @param    eid    element id
    # @param    lsid    the sibling id on the left
    # @param    text    text value
    # @param    value    hash value
    def addText(self, eid, lsid, text, value):
        self._elementIndex += 1
        topid = self._elementIndex / self._botCap
        botid = self._elementIndex % self._botCap
        if (botid == 0):
            self._expand(topid)

        etopid = eid / self._botCap
        ebotid = eid % self._botCap
        if (lsid == NULL_NODE):
            self._firstChild[etopid][ebotid] = self._elementIndex
        else:
            self._nextSibling[lsid / self._botCap][lsid % self._botCap] = self._elementIndex

        self._childrenCount[etopid][ebotid] += 1
        self._hashValue[topid][botid] = value

        self._valueCount += 1
        vtopid = self._valueCount / self._botCap
        vbotid = self._valueCount % self._botCap
        if (vbotid == 0):
            self._value[vtopid] = str[self._botCap]

        self._value[vtopid][vbotid] = text
        self._valueIndex[topid][botid] = self._valueCount

        return self._elementIndex

    # Add an attribute.
    # @param    eid    element id
    # @param    lsid    the sibling id on the left
    # @param    name    attribute name
    # @param    value    attribute value
    # @param    valuehash    hash value of the value
    # @param    attrhash    hash value of the entire attribute
    # @return    the element id of the attribute
    def addAttribute(self, eid, lsid, name, value, valuehash, attrhash):
        # attribute name first.
        aid = self.addElement(eid, lsid, name)

        # attribute value second.
        self.addText(aid, NULL_NODE, value, valuehash)

        # hash value third
        atopid = aid / self._botCap
        abotid = aid % self._botCap
        self._isAttribute[atopid][abotid] = True
        self._hashValue[atopid][abotid] = attrhash

        return aid

    # Add more information (hash value) to an element node.
    # @param    eid    element id
    # @param    value    extra hash value
    def addHashValue(self, eid, value):
        self._hashValue[eid / self._botCap][eid % self._botCap] = value

    # Add a CDATA section (either a start or an end) to the CDATA
    # hashtable, in which each entry should have an even number of
    # position slots.
    # @param    eid        The text node id
    # @param    position    the section tag position
    def addCDATA(self, eid, position):
        key = int(eid)
        value = self._cdataTable[key]
        if (value == None):
            elem_list = []
            elem_list.append(position)
            self._cdataTable[key] = elem_list
        else:
            elem_list = value
            elem_list.append(position)
            self._cdataTable[key] = elem_list

    # Add matching information.
    # @param    eid    element id
    # @param    match    ?match and matched element id
    def addMatching(self, eid, match):
        if (match[0] == NO_MATCH):
            self._matching[eid / self._botCap][eid % self._botCap] = NO_MATCH
        elif (match[0] == MATCH):
            self._matching[eid / self._botCap][eid % self._botCap] = MATCH
        else:
            self._matching[eid / self._botCap][eid % self._botCap] = match[1] + 1

    # End  -- methods for constructing a tree.

    # Start -- methods for accessing a tree.

    # Get matching information.
    # @param    eid    element id
    # @param    match    ?change and matched element id 
    def getMatching(self, eid, match):
        mid = self._matching[eid / self._botCap][eid % self._botCap]
        if (mid == NO_MATCH):
            match[0] = NO_MATCH
        elif (mid == MATCH):
            match[0] = MATCH
        else:
            match[0] = CHANGE
            match[1] = mid - 1

    # Get the root element id.
    def getRoot(self):
        return self._root

    # Get the first child of a node.
    # @param    eid    element id
    def getFirstChild(self, eid):
        cid = self._firstChild[eid / self._botCap][eid % self._botCap]
        while (cid > self._root):
            ctopid = cid / self._botCap
            cbotid = cid % self._botCap
            if (self._isAttribute[ctopid][cbotid]):
                cid = self._nextSibling[ctopid][cbotid]
            else:
                return cid

        return NULL_NODE

    # Get the next sibling of a node.
    # @param    eid    element id
    def getNextSibling(self, eid):
        return self._nextSibling[eid / self._botCap][eid % self._botCap]

    # Get the first attribute of a node.
    # @param    eid    element id
    def getFirstAttribute(self, eid):
        aid = self._firstChild[eid / self._botCap][eid % self._botCap]
        if ((aid > self._root) and (self._isAttribute[aid / self._botCap][aid % self._botCap])):
            return aid
        else:
            return NULL_NODE

    # Get the next attribute of a node.
    # @param    aid    attribute id
    def getNextAttribute(self, aid):
        aid1 = self._nextSibling[aid / self._botCap][aid % self._botCap]
        if ((aid1 > self._root) and (self._isAttribute[aid1 / self._botCap][aid1 % self._botCap])):
            return aid1
        else:
            return NULL_NODE

    # Get the attribute value.
    # @param    aid    attribute id
    def getAttributeValue(self, aid):
        cid = self._firstChild[aid / self._botCap][aid % self._botCap]
        index = self._valueIndex[cid / self._botCap][cid % self._botCap]
        if (index > 0):
            return self._value[index / self._botCap][index % self._botCap]
        else:
            return ""

    # Get the hash value of a node.
    # @param    eid    element id
    def getHashValue(self, eid):
        return self._hashValue[eid / self._botCap][eid % self._botCap]

    # Get the CDATA section position list of a text node.
    # @param    eid    element id
    # @return    position list which is a vector or None if no CDATA
    def getCDATA(self, eid):
        return self._cdataTable[eid]

    # Get the childern count of a node.
    # @param    eid    element id
    def getChildrenCount(self, eid):
        return self._childrenCount[eid / self._botCap][eid % self._botCap]

    # Get the # of all decendents of a node.
    # @param    eid    element id
    def getDecendentsCount(self, eid):
        topid = eid / self._botCap
        botid = eid % self._botCap
        count = self._childrenCount[topid][botid]
        if (count == 0):
            return 0

        cid = self._firstChild[topid][botid]
        while (cid > NULL_NODE):
            count += self.getDecendentsCount(cid)
            cid = self._nextSibling[cid / self._botCap][cid % self._botCap]

        return count

    # Get the value index of a node
    # @param    eid    element id
    def getValueIndex(self, eid):
        return self._valueIndex[eid / self._botCap][eid % self._botCap]

    # Get the value of a leaf node
    # @param    index    value index
    def getValue(self, index):
        return self._value[index / self._botCap][index % self._botCap]

    # Get the tag of an element node
    # @param    eid    element id
    def getTag(self, eid):
        index = self._valueIndex[eid / self._botCap][eid % self._botCap]
        return    self._value[0][index]

    # Get the text value of a leaf node
    # @param    eid    element id
    def getText(self, eid):
        index = self._valueIndex[eid / self._botCap][eid % self._botCap]
        if (index >= self._botCap):
            return self._value[index / self._botCap][index % self._botCap]
        else:
            return ""

    # Check if a node an element node.
    # @param    eid    element id
    def isElement(self, eid):
        vindex = self._valueIndex[eid / self._botCap][eid % self._botCap]
        if (vindex < self._botCap):
            return True
        else:
            return False

    # Check if a node is an attribute node.
    # @param    eid    element id
    def isAttribute(self, eid):
        return self._isAttribute[eid / self._botCap][eid % self._botCap]

    # Check if a node an leaf text node.
    # @param    edi    element id
    def isLeaf(self, eid):
        index = self._valueIndex[eid / self._botCap][eid % self._botCap]
        if (index < self._botCap):
            return False
        else:
            return True

    # End  -- methods for accessing a tree.

    # For testing purpose.
    def dump(self, eid=None):
        if eid:
            topid = eid / self._botCap
            botid = eid % self._botCap
            vid = self._valueIndex[topid][botid]
            vtopid = vid / self._botCap
            vbotid = vid % self._botCap
            print eid + "\t" + \
                       self._firstChild[topid][botid] + "\t" + \
                       self._nextSibling[topid][botid] + "\t" + \
                       self._isAttribute[topid][botid] + "\t" + \
                       self._childrenCount[topid][botid] + "\t" + \
                       self._hashValue[topid][botid] + "\t" + \
                       self._matching[topid][botid] + "\t" + \
                       self._value[vtopid][vbotid]
        else:
            print "eid\tfirstC\tnextS\tattr?\tcCount\thash\tmatch\tvalue"
            for i in range(self._root, self._elementIndex + 1):
                topid = i / self._botCap
                botid = i % self._botCap
                vid = self._valueIndex[topid][botid]
                vtopid = vid / self._botCap
                vbotid = vid % self._botCap
                print i + "\t" + \
                           self._firstChild[topid][botid] + "\t" + \
                           self._nextSibling[topid][botid] + "\t" + \
                           self._isAttribute[topid][botid] + "\t" + \
                           self._childrenCount[topid][botid] + "\t" + \
                           self._hashValue[topid][botid] + "\t" + \
                           self._matching[topid][botid] + "\t" + \
                           self._value[vtopid][vbotid]

