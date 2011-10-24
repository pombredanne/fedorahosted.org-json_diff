#!/usr/bin/env python
"""
java XDiff [-o|-g] [-p percent] [-e encoding] xml_file1 xml_file2 diff_result
Options:
  The default setting is "-o -p 0.3 -e UTF8"
  -o    The optimal mode, to get the minimum editing distance.
  -g    The greedy mode, to find a difference quickly.
  -p    The maximum change percentage allowed.
        Default value: 1.0 for -o mode; 0.3 for -g mode.
  -e    The encoding of the output file.
        Default value: UTF8.
"""
# Copyright (c) 2001 - 2005
#     Yuan Wang. All rights reserved.

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


#import java.io.BufferedReader
#import java.io.FileReader
#import java.io.FileOutputStream
#import java.io.OutputStreamWriter
#import java.io.IOException
#import java.util.Random
#import java.util.Vector
import sys, time, codecs
import XTree, XLut
from XParser import XParser
import random

# <code>XDiff</code> computes the difference of two input XML documents.

_CIRCUIT_SIZE = 2048
_MATRIX_SIZE = 1024
_ATTRIBUTE_SIZE = 1024
_TEXT_SIZE = 1024


class XDiff:
    _oFlag = False
    _gFlag = False
    _needNewLine = False
    _NO_MATCH_THRESHOLD = 0.3
    _sampleCount = 3
    _DEBUG = False
    _encoding = "UTF8"

#    self._xtree1, self._xtree2
#    private XLut    _xlut
#    private _leastCostMatrix[][], self._pathMatrix[][], self._circuit[]
#
#    private _attrList1[], _attrList2[], _textList1[], _textList2[]
#    private boolean _attrMatch[], _textMatch1[], _textMatch2[]
#    private long    _attrHash[], _textHash[]
#    private String    _attrTag[]
#
#    private self._matchp[]
#    private boolean    self._needNewLine



    # Constructor
    # @param    input1        input file #1
    # @param    input2        input file #2
    # @param    output        output file

    def __init__(self, input1, input2, output):
        # Parse input files
        parser = XParser()
        t0 = time.time()
        self._xtree1 = parser.parse(input1)
        t1 = time.time()
        parser = XParser()
        self._xtree2 = parser.parse(input2)
        t2 = time.time()

        # check both root nodes.
        root1 = self._xtree1.getRoot()
        root2 = self._xtree2.getRoot()
        if (self._xtree1.getHashValue(root1) == self._xtree2.getHashValue(root2)):
            print "No difference!"
            print "Execution time: " + (t2 - t0) + " ms"
            print "Parsing " + input1 + ": " + (t1 - t0) + " ms"
            print "Parsing " + input2 + ": " + (t2 - t1) + " ms"
        else:
            self._xlut =  XLut.XLut()
            self._matchp =  int[2]

            if (self._xtree1.getTag(root1).compareTo(self._xtree2.getTag(root2)) != 0):
                print "The root is changed!"
                self._matchp[0] = XTree.NO_MATCH
                self._xtree1.addMatching(root1, self._matchp)
                self._xtree2.addMatching(root2, self._matchp)
            else:
                # initialize data structures.
                self._attrList1    =  []
                self._attrList2    =  []
                self._attrMatch    =  []
                self._attrHash    =  []
                self._attrTag    =  []

                self._textList1    =  []
                self._textList2    =  []
                self._textMatch1    =  []
                self._textMatch2    =  []
                self._textHash    =  []

                self._leastCostMatrix =  []
                self._pathMatrix     =  []
                self._circuit     =  []

                for i in range(_MATRIX_SIZE):
                    self._leastCostMatrix[i] =  int[_MATRIX_SIZE]
                    self._pathMatrix[i] =  int[_MATRIX_SIZE]

                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = root2
                self._xtree1.addMatching(root1, self._matchp)
                self._matchp[1] = root1
                self._xtree2.addMatching(root2, self._matchp)
                self.xdiff(root1, root2, False)

            t3 = time.time()
            self.writeDiff(input1, output)
            t4 = time.time()

            print "Difference detected!"
            print "Execution time: " + (t4 - t0) + " ms"
            print "Parsing " + input1 + ": " + (t1 - t0) + " ms"
            print "Parsing " + input2 + ": " + (t2 - t1) + " ms"
            print "Diffing: " + (t3 - t2) + " ms"
            print "Writing result: " + (t4 - t3) + " ms"


    # Diff two element lists
    # This is the official one that records matching top-down
    # @param    pid1        parent id #1
    # @param    pid2        parent id #2
    # @param    matchFlag    indicates if distance computation needed
    def xdiff(self, pid1, pid2, matchFlag):
        # diff attributes.
        attrCount1 = 0
        attrCount2 = 0
        attr1 = self._xtree1.getFirstAttribute(pid1)
        while (attr1 != XTree.NULL_NODE):
            self._attrList1[attrCount1] = attr1
            attrCount1 += 1
            attr1 = self._xtree1.getNextAttribute(attr1)
        attr2 = self._xtree2.getFirstAttribute(pid2)
        while (attr2 != XTree.NULL_NODE):
            self._attrList2[attrCount2] = attr2
            attrCount2 += 1
            attr2 = self._xtree2.getNextAttribute(attr2)

        if (attrCount1 > 0):
            if (attrCount2 > 0):
                self.diffAttributes(attrCount1, attrCount2)
            else:
                self._matchp[0] = XTree.NO_MATCH
                for i in range(attrCount1):
                    self._xtree1.addMatching(self._attrList1[i],
                                self._matchp)
        elif (attrCount2 > 0):    # attrCount1 == 0
            self._matchp[0] = XTree.NO_MATCH
            for i in range(attrCount2):
                self._xtree2.addMatching(self._attrList2[i], self._matchp)

        # Match element nodes.
        count1 = self._xtree1.getChildrenCount(pid1) - attrCount1
        count2 = self._xtree2.getChildrenCount(pid2) - attrCount2

        if (count1 == 0):
            self._matchp[0] = XTree.NO_MATCH
            node2 = self._xtree2.getFirstChild(pid2)
            self._xtree2.addMatching(node2, self._matchp)
            for i in range(1,count2):
                node2 = self._xtree2.getNextSibling(node2)
                self._xtree2.addMatching(node2, self._matchp)
        elif (count2 == 0):
            self._matchp[0] = XTree.NO_MATCH
            node1 = self._xtree1.getFirstChild(pid1)
            self._xtree1.addMatching(node1, self._matchp)
            for i in range(1, count1):
                node1 = self._xtree1.getNextSibling(node1)
                self._xtree1.addMatching(node1, self._matchp)
        elif ((count1 == 1) and (count2 == 1)):
            node1 = self._xtree1.getFirstChild(pid1)
            node2 = self._xtree2.getFirstChild(pid2)

            if (self._xtree1.getHashValue(node1) == self._xtree2.getHashValue(node2)):
                return

            isE1 = self._xtree1.isElement(node1)
            isE2 = self._xtree2.isElement(node2)

            if (isE1 and isE2):
                tag1 = self._xtree1.getTag(node1)
                tag2 = self._xtree2.getTag(node2)
                if (tag1.compareTo(tag2) == 0):
                    self._matchp[0] = XTree.CHANGE
                    self._matchp[1] = node2
                    self._xtree1.addMatching(node1, self._matchp)
                    self._matchp[1] = node1
                    self._xtree2.addMatching(node2, self._matchp)

                    self.xdiff(node1, node2, matchFlag)
                else:
                    self._matchp[0] = XTree.NO_MATCH
                    self._xtree1.addMatching(node1, self._matchp)
                    self._xtree2.addMatching(node2, self._matchp)
            elif (not isE1 and not isE2):
                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = node2
                self._xtree1.addMatching(node1, self._matchp)
                self._matchp[1] = node1
                self._xtree2.addMatching(node2, self._matchp)
            else:
                self._matchp[0] = XTree.NO_MATCH
                self._xtree1.addMatching(node1, self._matchp)
                self._xtree2.addMatching(node2, self._matchp)
        else:
            elements1 =  int[count1]
            elements2 =  int[count2]
            elementCount1 = 0
            textCount1 = 0
            elementCount2 = 0
            textCount2 = 0

            child1 = self._xtree1.getFirstChild(pid1)
            if (self._xtree1.isElement(child1)):
                elements1[elementCount1] = child1
                elementCount1 += 1
            else:
                self._textList1[textCount1] = child1
                textCount1 += 1
            for i in range(1,count1):
                child1 = self._xtree1.getNextSibling(child1)
                if (self._xtree1.isElement(child1)):
                    elements1[elementCount1] = child1
                    elementCount1 += 1
                else:
                    self._textList1[textCount1] = child1
                    textCount1 += 1

            child2 = self._xtree2.getFirstChild(pid2)
            if (self._xtree2.isElement(child2)):
                elements2[elementCount2] = child2
                elementCount2 += 1
            else:
                self._textList2[textCount2] = child2
                textCount2 += 1
            for i in range(1,count2):
                child2 = self._xtree2.getNextSibling(child2)
                if (self._xtree2.isElement(child2)):
                    elements2[elementCount2] = child2
                    elementCount2 += 1
                else:
                    self._textList2[textCount2] = child2
                    textCount2 += 1

            # Match text nodes.
            if (textCount1 > 0):
                if (textCount2 > 0):
                    self.diffText(textCount1, textCount2)
                else:
                    self._matchp[0] = XTree.NO_MATCH
                    for i in range(textCount1):
                        self._xtree1.addMatching(self._textList1[i], self._matchp)
            elif (textCount2 > 0):
                self._matchp[0] = XTree.NO_MATCH
                for i in (textCount2):
                    self._xtree2.addMatching(self._textList2[i],
                                self._matchp)

            matched1 =  []
            matched2 =  []
            mcount = self._matchFilter(elements1, elementCount1,
                              elements2, elementCount2,
                              matched1, matched2)

            if ((elementCount1 == mcount) and (elementCount2 == mcount)):
                return

            if (elementCount1 == mcount):
                self._matchp[0] = XTree.NO_MATCH
                for i in range(elementCount2):
                    if (not matched2[i]):
                        self._xtree2.addMatching(elements2[i], self._matchp)
                return
            if (elementCount2 == mcount):
                self._matchp[0] = XTree.NO_MATCH
                for i in range(elementCount1):
                    if (not matched1[i]):
                        self._xtree1.addMatching(elements1[i], self._matchp)
                return

            # Write the list of unmatched nodes.
            ucount1 = elementCount1 - mcount
            ucount2 = elementCount2 - mcount
            unmatched1 =  int[ucount1]
            unmatched2 =  int[ucount2]
            muc1 = 0
            muc2 = 0
            start = 0

            while ((muc1 < ucount1) and (muc2 < ucount2)):
                while (start < elementCount1) and matched1[start]:
                    start += 1
                startTag = self._xtree1.getTag(elements1[start])
                uele1 = 0
                uele2 = 0
                muc1 += 1
                unmatched1[uele1] = elements1[start]
                uele1 += 1
                matched1[start] = True
                start += 1

                i = start
                while (i < elementCount1) and (muc1 < ucount1):
                    if (not matched1[i] and (startTag == self._xtree1.getTag(elements1[i]))):
                        matched1[i] = True
                        muc1 += 1
                        unmatched1[uele1] = elements1[i]
                        uele1 += 1
                    i += 1

                i = 0
                while (i < elementCount2) and (muc2 < ucount2):
                    if (not matched2[i] and (startTag == self._xtree2.getTag(elements2[i]))):
                        matched2[i] = True
                        muc2 += 1
                        unmatched2[uele2] = elements2[i]
                        uele2 += 1
                    i += 1

                if (uele2 == 0):
                    self._matchp[0] = XTree.NO_MATCH
                    for i in range(uele1):
                        self._xtree1.addMatching(unmatched1[i], self._matchp)
                else:
                    if ((uele1 == 1) and (uele2 == 1)):
                        self._matchp[0] = XTree.CHANGE
                        self._matchp[1] = unmatched2[0]
                        self._xtree1.addMatching(unmatched1[0], self._matchp)
                        self._matchp[1] = unmatched1[0]
                        self._xtree2.addMatching(unmatched2[0], self._matchp)
                        self.xdiff(unmatched1[0],
                              unmatched2[0],
                              matchFlag)
                    # To find minimal-cost matching between those unmatched.
                    elif (uele1 >= uele2):
                        if ((uele2 <= self._sampleCount) or not self._gFlag):
                            self.matchListO(unmatched1, unmatched2, uele1, uele2, True, matchFlag)
                        else:
                            self.matchList(unmatched1, unmatched2, uele1, uele2, True, matchFlag)
                    else:
                        if ((uele1 <= self._sampleCount) or not self._gFlag):
                            self.matchListO(unmatched2, unmatched1, uele2, uele1, False, matchFlag)
                        else:
                            self.matchList(unmatched2, unmatched1, uele2, uele1, False, matchFlag)

            if (muc1 < ucount1):
                self._matchp[0] = XTree.NO_MATCH
                for i in range(start,elementCount1):
                    if (not matched1[i]):
                        self._xtree1.addMatching(elements1[i], self._matchp)
            elif (muc2 < ucount2):
                self._matchp[0] = XTree.NO_MATCH
                for i in range(elementCount2):
                    if (not matched2[i]):
                        self._xtree2.addMatching(elements2[i], self._matchp)


    # Diff and match two lists of attributes
    # @param    attrCount1    number of attributes in the 1st list
    # @param    attrCount2    number of attributes in the 2nd list
    def diffAttributes(self, attrCount1,  attrCount2):
        if ((attrCount1 == 1) and (attrCount2 == 1)):
            ah1 = self._xtree1.getHashValue(self._attrList1[0])
            ah2 = self._xtree2.getHashValue(self._attrList2[0])
            if (ah1 == ah2):
                return

            tag1 = self._xtree1.getTag(self._attrList1[0])
            tag2 = self._xtree2.getTag(self._attrList2[0])
            if (tag1.compareTo(tag2) == 0):
                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = self._attrList2[0]
                self._xtree1.addMatching(self._attrList1[0], self._matchp)

                self._matchp[1] = self._attrList1[0]
                self._xtree2.addMatching(self._attrList2[0], self._matchp)

                tid1 = self._xtree1.getFirstChild(self._attrList1[0])
                tid2 = self._xtree2.getFirstChild(self._attrList2[0])
                self._matchp[1] = tid2
                self._xtree1.addMatching(tid1, self._matchp)

                self._matchp[1] = tid1
                self._xtree2.addMatching(tid2, self._matchp)

                return
            else:
                self._matchp[0] = XTree.NO_MATCH
                self._xtree1.addMatching(self._attrList1[0], self._matchp)
                self._xtree2.addMatching(self._attrList2[0], self._matchp)
                return

        for i in range(attrCount2):
            self._attrHash[i] = self._xtree2.getHashValue(self._attrList2[i])
            self._attrTag[i] = self._xtree2.getTag(self._attrList2[i])
            self._attrMatch[i] = False

        matchCount = 0
        for i in range(attrCount1):
            attr1 = self._attrList1[i]
            ah1 = self._xtree1.getHashValue(attr1)
            tag1 = self._xtree1.getTag(attr1)

            found = False
            for j in range(attrCount2):
                attr2 = self._attrList2[j]
                if (self._attrMatch[j]):
                    continue
                elif (ah1 == self._attrHash[j]):
                    self._attrMatch[j] = True
                    matchCount += 1
                    found = True
                    break
                elif (tag1.compareTo(self._attrTag[j]) == 0):
                    self._attrMatch[j] = True
                    matchCount += 1

                    self._matchp[0] = XTree.CHANGE
                    self._matchp[1] = attr2
                    self._xtree1.addMatching(attr1, self._matchp)

                    self._matchp[1] = attr1
                    self._xtree2.addMatching(attr2, self._matchp)

                    tid1 = self._xtree1.getFirstChild(attr1)
                    tid2 = self._xtree2.getFirstChild(attr2)
                    self._matchp[1] = tid2
                    self._xtree1.addMatching(tid1, self._matchp)

                    self._matchp[1] = tid1
                    self._xtree2.addMatching(tid2, self._matchp)

                    found = True
                    break

            if (not found):
                self._matchp[0] = XTree.NO_MATCH
                self._xtree1.addMatching(attr1, self._matchp)

        if (matchCount != attrCount2):
            self._matchp[0] = XTree.NO_MATCH
            for i in range(attrCount2):
                if (not self._attrMatch[i]):
                    self._xtree2.addMatching(self._attrList2[i],
                                self._matchp)

    # Diff and match two lists of text nodes.
    # XXX This is just a hack that treats text nodes as unordered, to
    # be consistent with the entire algorithm.
    # @param    textCount1    number of text nodes in the 1st list
    # @param    textCount2    number of text nodes in the 2nd list

    def diffText(self, textCount1, textCount2):
        for i in range(textCount1):
            self._textMatch1[i] = False
        for i in range(textCount2):
            self._textMatch2[i] = False
            self._textHash[i] = self._xtree2.getHashValue(self._textList2[i])

        mcount = 0
        for i in range(textCount1):
            hash1 = self._xtree1.getHashValue(self._textList1[i])
            for j in range(textCount2):
                if (not self._textMatch2[j] and (hash1 == self._textHash[j])):
                    self._textMatch1[i] = True
                    self._textMatch2[j] = True
                    mcount += 1
                    break

            if (mcount == textCount2):
                break

        if ((mcount < textCount1) and (textCount1 <= textCount2)):
            self._matchp[0] = XTree.CHANGE
            i = 0
            j = 0
            while (i < textCount1) and (mcount < textCount1):
                if (self._textMatch1[i]):
                    continue
                while self._textMatch2[j]:
                    j += 1
                self._matchp[1] = self._textList2[j]
                self._xtree1.addMatching(self._textList1[i], self._matchp)
                self._textMatch1[i] = True
                self._matchp[1] = self._textList1[i]
                self._xtree2.addMatching(self._textList2[j], self._matchp)
                self._textMatch2[j] = True
                mcount += 1
                i += 1
        elif ((mcount < textCount2) and (textCount2 < textCount1)):
            self._matchp[0] = XTree.CHANGE
            i = 0
            j = 0
            while (i < textCount2) and (mcount < textCount2):
                if (self._textMatch2[i]):
                    continue
                while (self._textMatch1[j]):
                    j += 1
                self._matchp[1] = self._textList1[j]
                self._xtree2.addMatching(self._textList2[i], self._matchp)
                self._textMatch2[i] = True
                self._matchp[1] = self._textList2[i]
                self._xtree1.addMatching(self._textList1[j], self._matchp)
                self._textMatch1[j] = True
                mcount += 1
                i += 1

        self._matchp[0] = XTree.NO_MATCH
        if (mcount < textCount1):
            for i in range(textCount1):
                if (not self._textMatch1[i]):
                    self._xtree1.addMatching(self._textList1[i],
                                self._matchp)
        elif (mcount < textCount2):
            for i in range(textCount2):
                if (not self._textMatch2[i]):
                    self._xtree2.addMatching(self._textList2[i],
                                self._matchp)


    # Filter out matched nodepairs.
    # @param    elements1    node list #1
    # @param    elements2    node list #2
    # @param    matched1    match list #1
    # @param    matched2    match list #2
    # @return    how many matched pairs found

    def _matchFilter(self, elements1, count1, elements2, count2, matched1, matched2):
        value1 =  int[count1]
        value2 =  int[count2]

        for i in range(count1):
            value1[i] = self._xtree1.getHashValue(elements1[i])
            matched1[i] = False
        for i in range(count2):
            value2[i] = self._xtree2.getHashValue(elements2[i])
            matched2[i] = False

        mcount = 0
        for i in range(count2):
            for j in range (count1):
                if (not matched1[j] and not matched2[i] and (value1[j] == value2[i])):
                    matched1[j] = True
                    matched2[i] = True
                    mcount += 1
                    break

        return mcount


    # Find minimal cost matching between two node lists
    # Record the matching info back to the trees
    # Using the original algorithm
    # @param    nodes1        node list #1
    # @param    nodes2        node list #2
    # @param    count1        # of nodes in node list #1
    # @param    count2        # of nodes in node list #2
    # @param    treeOrder    True for original, False for inverse
    # @param    matchFlag    indicates if distance computation needed

    def matchListO(self, nodes1, nodes2, count1, count2, treeOrder, matchFlag):
        distance =  []
        matching1 =  []
        matching2 =  []

        # insert cost.
        distance[count1] =  int[count2+1]
        for i in range(count2):
            if treeOrder:
                distance[count1][i] = self._xtree2.getDecendentsCount(nodes2[i])
            else:
                distance[count1][i] = self._xtree1.getDecendentsCount(nodes2[i]) + 1

        for i in range(count1):
            distance[i] =  int[count2+1]
            if treeOrder:
                deleteCost = self._xtree1.getDecendentsCount(nodes1[i])
            else:
                deleteCost = self._xtree2.getDecendentsCount(nodes1[i]) + 1
            for j in range(count2):
                dist = 0
                if (matchFlag):
                    if treeOrder:
                        dist = self._xlut.get(nodes1[i], nodes2[j])
                    else:
                        dist = self._xlut.get(nodes2[j], nodes1[i])
                else:
                    if treeOrder:
                        dist = self.distance(nodes1[i], nodes2[j], True, XTree.NO_CONNECTION)
                    else:
                        dist = self.distance(nodes2[j], nodes1[i], True, XTree.NO_CONNECTION)
                    # the default mode.
                    if (not self._oFlag and (dist > 1) and (dist >= self._NO_MATCH_THRESHOLD * (deleteCost + distance[count1][j]))):
                        dist = XTree.NO_CONNECTION
                    if (dist < XTree.NO_CONNECTION):
                        if (treeOrder):
                            self._xlut.add(nodes1[i],
                                  nodes2[j],
                                  dist)
                        else:
                            self._xlut.add(nodes2[j],
                                  nodes1[i],
                                  dist)
                distance[i][j] = dist
            # delete cost.
            distance[i][count2] = deleteCost

        # compute the minimal cost matching.
        self.findMatching(count1, count2, distance, matching1, matching2)

        for i in range(count1):
            if (matching1[i] == XTree.NO_MATCH):
                self._matchp[0] = XTree.NO_MATCH
            else:
                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = nodes2[matching1[i]]
            if (treeOrder):
                self._xtree1.addMatching(nodes1[i], self._matchp)
            else:
                self._xtree2.addMatching(nodes1[i], self._matchp)

        for i in range(count2):
            if (matching2[i] == XTree.NO_MATCH):
                self._matchp[0] = XTree.NO_MATCH
            else:
                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = nodes1[matching2[i]]
            if (treeOrder):
                self._xtree2.addMatching(nodes2[i], self._matchp)
            else:
                self._xtree1.addMatching(nodes2[i], self._matchp)

        for i in range(count1):
            if (matching1[i] != XTree.NO_MATCH):
                todo1 = nodes1[i]
                todo2 = nodes2[matching1[i]]
                if (treeOrder):
                    if (self._xtree1.isElement(todo1) and self._xtree2.isElement(todo2)):
                        self.xdiff(todo1, todo2, True)
                else:
                    if (self._xtree1.isElement(todo2) and self._xtree2.isElement(todo1)):
                        self.xdiff(todo2, todo1, True)


    # Find minimal cost matching between two node lists
    # Record the matching info back to the trees
    # Do sampling.
    # @param    nodes1        node list #1
    # @param    nodes2        node list #2
    # @param    count1        # of nodes in node list #1
    # @param    count2        # of nodes in node list #2
    # @param    treeOrder    True for original, False for inverse
    # @param    matchFlag    indicates if distance computation needed

    def matchList(self, nodes1, nodes2, count1, count2, treeOrder, matchFlag):
        matching1 =  []
        matching2 =  []
        for i in range(count1):
            matching1[i] = XTree.NO_MATCH
        for i in range(count2):
            matching2[i] = XTree.NO_MATCH

        if (matchFlag):
            for i in range(count1):
                for j in range(count2):
                    if treeOrder:
                        d = self._xlut.get(nodes1[i], nodes2[j])
                    else: 
                        d = self._xlut.get(nodes2[j], nodes1[i])
                    if (d != XTree.NO_CONNECTION):
                        matching1[i] = j
                        matching2[j] = i
                        break
        else:
            r =  random.Random(time.time())
            scount1 = 0
            scount2 = 0
            matchingThreshold = 0
            i = 0
            while (i < self._sampleCount) and (scount2 < count2):
                snode = r.randint(0, count2 - scount2) + scount2
                dist = XTree.NO_CONNECTION
                bestmatch = XTree.NO_MATCH
                for j in range(scount1,count1):
                    if treeOrder:
                        d = self.distance(nodes1[j], nodes2[snode], False, dist)
                    else:
                        d = self.distance(nodes2[snode], nodes1[j], False, dist)
                    if (d < dist):
                        dist = d
                        bestmatch = j
                        if (d == 1):
                            break
                scount2 += 1

                if treeOrder:
                    deleteCost = self._xtree2.getDecendentsCount(nodes2[snode]) + 1
                else:
                    deleteCost = self._xtree1.getDecendentsCount(nodes2[snode]) + 1
                if ((dist > 1) and (dist > (self._NO_MATCH_THRESHOLD * deleteCost))):
                    tmp = nodes2[snode]
                    nodes2[snode] = nodes2[scount2]
                    nodes2[scount2] = tmp
                else:
                    tmp = nodes1[bestmatch]
                    nodes1[bestmatch] = nodes1[scount1]
                    nodes1[scount1] = tmp
                    tmp = nodes2[snode]
                    nodes2[snode] = nodes2[scount2]
                    nodes2[scount2] = tmp

                    if (treeOrder):
                        self._xlut.add(nodes1[scount1], nodes2[scount2], dist)
                    else:
                        self._xlut.add(nodes2[scount2], nodes1[scount1], dist)
                    matching1[scount1] = scount2
                    matching2[scount2] = scount1

                    i += 1
                    scount1 += 1
                    if (matchingThreshold < dist):
                        matchingThreshold = dist

            while scount2 < count2:
                dist = XTree.NO_CONNECTION
                bestmatch = XTree.NO_MATCH
                for i in range(scount1,count1):
                    if treeOrder:
                        d = self.distance(nodes1[i], nodes2[scount2], False, dist)
                    else:
                        d = self.distance(nodes2[scount2], nodes1[i], False, dist)
                    if (d <= matchingThreshold):
                        dist = d
                        bestmatch = i
                        break
                    elif (d < dist):
                        dist = d
                        bestmatch = i

                if (bestmatch != XTree.NO_MATCH):
                    tmp = nodes1[bestmatch]
                    nodes1[bestmatch] = nodes1[scount1]
                    nodes1[scount1] = tmp

                    if (treeOrder):
                        self._xlut.add(nodes1[scount1], nodes2[scount2], dist)
                    else:
                        self._xlut.add(nodes2[scount2], nodes1[scount1], dist)
                    matching1[scount1] = scount2
                    matching2[scount2] = scount1
                    scount1 += 1
                scount2 += 1

        # Record matching
        for i in range(count1):
            if (matching1[i] == XTree.NO_MATCH):
                self._matchp[0] = XTree.NO_MATCH
            else:
                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = nodes2[matching1[i]]
            if (treeOrder):
                self._xtree1.addMatching(nodes1[i], self._matchp)
            else:
                self._xtree2.addMatching(nodes1[i], self._matchp)

        for i in range(count2):
            if (matching2[i] == XTree.NO_MATCH):
                self._matchp[0] = XTree.NO_MATCH
            else:
                self._matchp[0] = XTree.CHANGE
                self._matchp[1] = nodes1[matching2[i]]
            if (treeOrder):
                self._xtree2.addMatching(nodes2[i], self._matchp)
            else:
                self._xtree1.addMatching(nodes2[i], self._matchp)

        for i in range(count1):
            if (matching1[i] != XTree.NO_MATCH):
                todo1 = nodes1[i]
                todo2 = nodes2[matching1[i]]
                if (treeOrder):
                    if (self._xtree1.isElement(todo1) and self._xtree2.isElement(todo2)):
                        self.xdiff(todo1, todo2, True)
                else:
                    if (self._xtree1.isElement(todo2) and self._xtree2.isElement(todo1)):
                        self.xdiff(todo2, todo1, True)


    # Compute (minimal-editing) distance between two nodes.
    # @param    eid1        element id #1
    # @param    eid2        element id #2
    # @param    toRecord    whether or not to keep the result
    # @param    threshold    No need to return a distance higher
    #                than this threshold
    # @return    the distance

    def distance(self, eid1, eid2, toRecord, threshold):
        isE1 = self._xtree1.isElement(eid1)
        isE2 = self._xtree2.isElement(eid2)
        if (isE1 and isE2):
            if (self._xtree1.getTag(eid1).compareTo(self._xtree2.getTag(eid2)) != 0):
                return XTree.NO_CONNECTION
            else:
                dist = self._xdiff(eid1, eid2, threshold)
                if (toRecord and (dist < XTree.NO_CONNECTION)):
                    self._xlut.add(eid1, eid2, dist)
                return dist
        elif (not isE1 and not isE2):
            return 1
        else:
            return XTree.NO_CONNECTION


    # To compute the editing distance between two nodes
    # @param    pid1        parent id #1
    # @param    pid2        parent id #2
    # @param    threshold    No need to return a distance higher
    #                  than this threshold
    # @return    the distance
    def _xdiff(self, pid1, pid2, threshold):
        dist = 0

        # diff attributes.
        attrCount1 = 0
        attrCount2 = 0
        attr1 = self._xtree1.getFirstAttribute(pid1)
        while (attr1 != XTree.NULL_NODE):
            self._attrList1[attrCount1] = attr1
            attrCount1 += 1
            attr1 = self._xtree1.getNextAttribute(attr1)
        attr2 = self._xtree2.getFirstAttribute(pid2)
        while (attr2 != XTree.NULL_NODE):
            self._attrList2[attrCount2] = attr2
            attrCount2 += 1
            attr2 = self._xtree2.getNextAttribute(attr2)

        if (attrCount1 == 0):
            dist = attrCount2 * 2
        elif (attrCount2 == 0):
            dist = attrCount1 * 2
        else:
            dist = self._diffAttributes(attrCount1, attrCount2)
        if (self._gFlag and (dist >= threshold)):
            return XTree.NO_CONNECTION

        # Match second level nodes first.
        count1 = self._xtree1.getChildrenCount(pid1) - attrCount1
        count2 = self._xtree2.getChildrenCount(pid2) - attrCount2

        if (count1 == 0):
            node2 = self._xtree2.getFirstChild(pid2)
            while (node2 != XTree.NULL_NODE):
                dist += self._xtree2.getDecendentsCount(node2) + 1
                if (self._gFlag and (dist >= threshold)):
                    return XTree.NO_CONNECTION
                node2 = self._xtree2.getNextSibling(node2)
        elif (count2 == 0):
            node1 = self._xtree1.getFirstChild(pid1)
            while (node1 != XTree.NULL_NODE):
                dist += self._xtree1.getDecendentsCount(node1) + 1
                if (self._gFlag and (dist >= threshold)):
                    return XTree.NO_CONNECTION
                node1 = self._xtree1.getNextSibling(node1)
        elif ((count1 == 1) and (count2 == 1)):
            node1 = self._xtree1.getFirstChild(pid1)
            node2 = self._xtree2.getFirstChild(pid2)

            if (self._xtree1.getHashValue(node1) == self._xtree2.getHashValue(node2)):
                return dist

            isE1 = self._xtree1.isElement(node1)
            isE2 = self._xtree2.isElement(node2)

            if (isE1 and isE2):
                tag1 = self._xtree1.getTag(node1)
                tag2 = self._xtree2.getTag(node2)
                if (tag1.compareTo(tag2) == 0):
                    dist += self._xdiff(node1, node2, threshold - dist)
                else:
                    dist += self._xtree1.getDecendentsCount(node1) + self._xtree2.getDecendentsCount(node2) + 2
            elif (not isE1 and not isE2):
                dist += 1
            else:
                dist += self._xtree1.getDecendentsCount(node1) + self._xtree2.getDecendentsCount(node2) + 2
        else:
            elements1 =  int[count1]
            elements2 =  int[count2]
            elementCount1 = 0
            textCount1 = 0
            elementCount2 = 0
            textCount2 = 0

            child1 = self._xtree1.getFirstChild(pid1)
            if (self._xtree1.isElement(child1)):
                elements1[elementCount1] = child1
                elementCount1 += 1
            else:
                self._textList1[textCount1] = child1
                textCount1 += 1
            for i in range(1,count1):
                child1 = self._xtree1.getNextSibling(child1)
                if (self._xtree1.isElement(child1)):
                    elements1[elementCount1] = child1
                    elementCount1 += 1
                else:
                    self._textList1[textCount1] = child1
                    textCount1 += 1

            child2 = self._xtree2.getFirstChild(pid2)
            if (self._xtree2.isElement(child2)):
                elements2[elementCount2] = child2
                elementCount2 += 1
            else:
                self._textList2[textCount2] = child2
                textCount2 += 1
            for i in range(1,count2):
                child2 = self._xtree2.getNextSibling(child2)
                if (self._xtree2.isElement(child2)):
                    elements2[elementCount2] = child2
                    elementCount2 += 1
                else:
                    self._textList2[textCount2] = child2
                    textCount2 += 1

            # Match text nodes.
            if (textCount1 == 0):
                dist += textCount2
            elif (textCount2 == 0):
                dist += textCount1
            else:
                dist += self._diffText(textCount1, textCount2)

            if (self._gFlag and (dist >= threshold)):
                return XTree.NO_CONNECTION

            matched1 =  []
            matched2 =  []
            mcount = self._matchFilter(elements1, elementCount1,
                              elements2, elementCount2,
                              matched1, matched2)

            if ((elementCount1 == mcount) and (elementCount2 == mcount)):
                return dist
            if (elementCount1 == mcount):
                for i in range(elementCount2):
                    if (not matched2[i]):
                        dist += self._xtree2.getDecendentsCount(elements2[i]) + 1
                        if (self._gFlag and (dist >= threshold)):
                            return XTree.NO_CONNECTION
                return dist
            if (elementCount2 == mcount):
                for i in range(elementCount1):
                    if (not matched1[i]):
                        dist += self._xtree1.getDecendentsCount(elements1[i]) + 1
                        if (self._gFlag and (dist >= threshold)):
                            return XTree.NO_CONNECTION
                return dist

            # Write the list of unmatched nodes.
            ucount1 = elementCount1 - mcount
            ucount2 = elementCount2 - mcount
            unmatched1 =  []
            unmatched2 =  []
            muc1 = 0
            muc2 = 0
            start = 0

            while ((muc1 < ucount1) and (muc2 < ucount2)):
                while (start < elementCount1) and matched1[start]:
                    start += 1
                startTag = self._xtree1.getTag(elements1[start])
                uele1 = 0
                uele2 = 0
                muc1 += 1
                unmatched1[uele1] = elements1[start]
                uele1 += 1
                matched1[start] = True
                start += 1

                i = start
                while (i < elementCount1) and (muc1 < ucount1):
                    if (not matched1[i] and (startTag == self._xtree1.getTag(elements1[i]))):
                        matched1[i] = True
                        muc1 += 1
                        unmatched1[uele1] = elements1[i]
                        uele1 += 1
                    i += 1

                i = 0
                while (i < elementCount2) and (muc2 < ucount2):
                    if (not matched2[i] and (startTag == self._xtree2.getTag(elements2[i]))):
                        matched2[i] = True
                        muc2 += 1
                        unmatched2[uele2] = elements2[i]
                        uele2 += 1
                    i += 1

                if (uele2 == 0):
                    for i in range(uele1):
                        dist += self._xtree1.getDecendentsCount(unmatched1[i])
                else:
#                    if ((uele1 == 1) and (uele2 == 1)):
#                        dist += self._xdiff(unmatched1[0],
#                               unmatched2[0],
#                               threshold-dist)
#                elif (uele1 >= uele2):
                # To find minimal-cost matching between those unmatched.
                    if (uele1 >= uele2):
                        if ((uele2 <= self._sampleCount) or not self._gFlag):
                            dist += self._matchListO(unmatched1, unmatched2, uele1, uele2, True)
                        else:
                            dist += self._matchList(unmatched1, unmatched2, uele1, uele2, True, threshold - dist)
                    else:
                        if ((uele1 <= self._sampleCount) or not self._gFlag):
                            dist += self._matchListO(unmatched2, unmatched1, uele2, uele1, False)
                        else:
                            dist += self._matchList(unmatched2, unmatched1, uele2, uele1, False, threshold - dist)

                if (self._gFlag and (dist >= threshold)):
                    return XTree.NO_CONNECTION

            if (muc1 < ucount1):
                for i in range (start,elementCount1):
                    if (not matched1[i]):
                        dist += self._xtree1.getDecendentsCount(elements1[i])
            elif (muc2 < ucount2):
                for i in range(elementCount2):
                    if (not matched2[i]):
                        dist += self._xtree2.getDecendentsCount(elements2[i])

        if (not self._gFlag or (dist < threshold)):
            return dist
        else:
            return XTree.NO_CONNECTION


    # Diff two lists of attributes
    # @param    attrCount1    number of attributes in the 1st list
    # @param    attrCount2    number of attributes in the 2nd list
    # @return    the distance

    def _diffAttributes(self, attrCount1, attrCount2):
        if ((attrCount1 == 1) and (attrCount2 == 1)):
            ah1 = self._xtree1.getHashValue(self._attrList1[0])
            ah2 = self._xtree2.getHashValue(self._attrList2[0])
            if (ah1 == ah2):
                return 0

            tag1 = self._xtree1.getTag(self._attrList1[0])
            tag2 = self._xtree2.getTag(self._attrList2[0])
            if (tag1.compareTo(tag2) == 0):
                return 1
            else:
                return 2

        dist = 0
        for i in range(attrCount2):
            self._attrHash[i] = self._xtree2.getHashValue(self._attrList2[i])
            self._attrTag[i] = self._xtree2.getTag(self._attrList2[i])
            self._attrMatch[i] = False

        matchCount = 0
        for i in range(attrCount1):
            ah1 = self._xtree1.getHashValue(self._attrList1[i])
            tag1 = self._xtree1.getTag(self._attrList1[i])
            found = False

            for j in range(attrCount2):
                if (self._attrMatch[j]):
                    continue
                elif (ah1 == self._attrHash[j]):
                    self._attrMatch[j] = True
                    found = True
                    matchCount += 1
                    break
                elif (tag1.compareTo(self._attrTag[j]) == 0):
                    self._attrMatch[j] = True
                    dist += 1
                    found = True
                    matchCount += 1
                    break

            if (not found):
                dist += 2

        dist += (attrCount2 - matchCount) * 2
        return dist


    # Diff and match two lists of text nodes.
    # XXX This is just a hack that treats text nodes as unordered, to
    # be consistent with the entire algorithm.
    # @param    textCount1    number of text nodes in the 1st list
    # @param    textCount2    number of text nodes in the 2nd list
    # @return the "distance" between these two lists.

    def _diffText(self, textCount1, textCount2):
        for i in range(textCount2):
            self._textMatch2[i] = False
            self._textHash[i] = self._xtree2.getHashValue(self._textList2[i])

        mcount = 0
        for i in range(textCount1):
            hash1 = self._xtree1.getHashValue(self._textList1[i])
            for j in range(textCount2):
                if (not self._textMatch2[j] and (hash1 == self._textHash[j])):
                    self._textMatch2[j] = True
                    mcount += 1
                    break

            if (mcount == textCount2):
                break

        if (textCount1 >= textCount2):
            return textCount1 - mcount
        else:
            return textCount2 - mcount


    # Find minimal cost matching between two node lists
    # Using the original algorithm
    # @param    nodes1        node list #1
    # @param    nodes2        node list #2
    # @param    count1        # of nodes in node list #1
    # @param    count2        # of nodes in node list #2
    # @param    treeOrder    True for original, False for inverse

    def _matchListO(self, nodes1, nodes2, count1, count2, treeOrder):
        distance =  []
        matching1 =  []
        matching2 =  []

        # insert cost.
        distance[count1] =  int[count2+1]
        for i in range(count2):
            if treeOrder:
                distance[count1][i] = self._xtree2.getDecendentsCount(nodes2[i]) + 1
            else:
                distance[count1][i] = self._xtree1.getDecendentsCount(nodes2[i]) + 1

        for i in range(count1):
            distance[i] =  int[count2+1]
            if treeOrder:
                deleteCost = self._xtree1.getDecendentsCount(nodes1[i]) + 1
            else:
                deleteCost = self._xtree2.getDecendentsCount(nodes1[i]) + 1
            for j in range(count2):
                if treeOrder:
                    dist = self.distance(nodes1[i], nodes2[j], True, XTree.NO_CONNECTION)
                else:
                    dist = self.distance(nodes2[j], nodes1[i], True, XTree.NO_CONNECTION)
                # the default mode.
                if (not self._oFlag and (dist > 1) and (dist < XTree.NO_CONNECTION) and \
                    (dist >= self._NO_MATCH_THRESHOLD * (deleteCost + distance[count1][j]))):
                        dist = XTree.NO_CONNECTION

                if (dist < XTree.NO_CONNECTION):
                    if (treeOrder):
                        self._xlut.add(nodes1[i], nodes2[j], dist)
                    else:
                        self._xlut.add(nodes2[j], nodes1[i], dist)
                distance[i][j] = dist

            # delete cost.
            distance[i][count2] = deleteCost

        # compute the minimal cost matching.
        return self.findMatching(count1, count2, distance, matching1,
                    matching2)


    # Find minimal cost matching between two node lists
    # Do sampling
    # @param    nodes1        node list #1
    # @param    nodes2        node list #2
    # @param    count1        # of nodes in node list #1
    # @param    count2        # of nodes in node list #2
    # @param    treeOrder    True for original, False for inverse
    # @param    threshold    No need to return a distance higher
    #                  than this threshold
    def _matchList(self, nodes1, nodes2, count1, count2, treeOrder, threshold):
        matching1 =  []
        matching2 =  []
        for i in range(count1):
            matching1[i] = XTree.NO_MATCH
        for i in range(count2):
            matching2[i] = XTree.NO_MATCH

        distance = 0
        r =  random.Random(time.time())
        scount1 = 0
        scount2 = 0
        matchingThreshold = 0

        i = 0
        while (i < self._sampleCount) and (scount2 < count2):
            snode = r.randint(0, count2 - scount2) + scount2
            dist = XTree.NO_CONNECTION
            bestmatch = XTree.NO_MATCH
            for j in range(scount1,count1):
                if treeOrder:
                    d = self.distance(nodes1[j], nodes2[snode], False, threshold - distance)
                else:
                    d = self.distance(nodes2[snode], nodes1[j], False, threshold - distance)
                if (d < dist):
                    dist = d
                    bestmatch = j
                    if (d == 1):
                        break

            if treeOrder:
                deleteCost = self._xtree2.getDecendentsCount(nodes2[snode]) + 1
                deleteCost =  self._xtree1.getDecendentsCount(nodes2[snode]) + 1

            if ((dist > 1) and (dist > (self._NO_MATCH_THRESHOLD * deleteCost))):
                tmp = nodes2[snode]
                nodes2[snode] = nodes2[scount2]
                nodes2[scount2] = tmp
                distance += deleteCost
            else:
                tmp = nodes1[bestmatch]
                nodes1[bestmatch] = nodes1[scount1]
                nodes1[scount1] = tmp
                tmp = nodes2[snode]
                nodes2[snode] = nodes2[scount2]
                nodes2[scount2] = tmp

                if (treeOrder):
                    self._xlut.add(nodes1[scount1], nodes2[scount2], dist)
                else:
                    self._xlut.add(nodes2[scount2], nodes1[scount1], dist)
                matching1[scount1] = scount2
                matching2[scount2] = scount1

                i += 1
                scount1 += 1
                if (matchingThreshold < dist):
                    matchingThreshold = dist
                distance += dist

            if (distance >= threshold):
                return XTree.NO_CONNECTION
            scount2 += 1

        while (scount2 < count2):
            if treeOrder:
                deleteCost = self._xtree2.getDecendentsCount(nodes2[scount2]) + 1
            else:
                deleteCost = self._xtree1.getDecendentsCount(nodes2[scount2]) + 1
            dist = XTree.NO_CONNECTION
            bestmatch = XTree.NO_MATCH
            for i in range(scount1,count1):
                if treeOrder:
                    d = distance(nodes1[i], nodes2[scount2], False, threshold - distance)
                else:
                    d = distance(nodes2[scount2], nodes1[i], False, threshold - distance)
                if (d <= matchingThreshold):
                    dist = d
                    bestmatch = i
                    break
                elif ((d == 1) or ( d < (self._NO_MATCH_THRESHOLD * dist))):
                    dist = d
                    bestmatch = i

            if (bestmatch == XTree.NO_MATCH):
                distance += deleteCost
            else:
                tmp = nodes1[bestmatch]
                nodes1[bestmatch] = nodes1[scount1]
                nodes1[scount1] = tmp

                if (treeOrder):
                    self._xlut.add(nodes1[scount1], nodes2[scount2], dist)
                else:
                    self._xlut.add(nodes2[scount2], nodes1[scount1], dist)

                matching1[scount1] = scount2
                matching2[scount2] = scount1
                scount1 += 1
                distance += dist

            if (distance >= threshold):
                return XTree.NO_CONNECTION
            scount2 += 1

        for i in range(count1):
            if (matching1[i] == XTree.NO_MATCH):
                if treeOrder:
                    distance += self._xtree1.getDecendentsCount(nodes1[i]) + 1
                else:
                    distance += self._xtree2.getDecendentsCount(nodes1[i]) + 1
                if (distance >= threshold):
                    return XTree.NO_CONNECTION

        return distance


    # Perform minimal-cost matching between two node lists #1
    # Trivial part.
    # @param    count1    length of node list #1
    # @param    count2    length of node list #2
    # @param    dist    distance matrix
    # @param    matching1    matching list (for node list #1)
    # @param    matching2    matching list (for node list #2)
    # @return    distance
    def findMatching(self, count1, count2, dist, matching1, matching2):
        if (count1 == 1):
            # count2 == 1
            if (dist[0][0] < XTree.NO_CONNECTION):
                matching1[0] = 0
                matching2[0] = 0
            else:
                matching1[0] = XTree.DELETE
                matching2[0] = XTree.DELETE

            return dist[0][0]
        elif (count2 == 1):
            distance = 0
            mate = 0
            mindist = XTree.NO_CONNECTION
            matching2[0] = XTree.DELETE

            for i in range(count1):
                matching1[i] = XTree.DELETE
                if (mindist > dist[i][0]):
                    mindist = dist[i][0]
                    mate = i

                # Suppose we delete every node on list1.
                distance += dist[i][1]

            if (mindist < XTree.NO_CONNECTION):
                matching1[mate] = 0
                matching2[0] = mate
                distance += mindist - dist[mate][1]
            else:
                # Add the delete cost of the single node
                # on list2.
                distance += dist[count1][0]

            return distance
        elif ((count1 == 2) and (count2 == 2)):
            distance1 = dist[0][0] + dist[1][1]
            distance2 = dist[0][1] + dist[1][0]
            if (distance1 < distance2):
                if (dist[0][0] < XTree.NO_CONNECTION):
                    matching1[0] = 0
                    matching2[0] = 0
                    distance1 = dist[0][0]
                else:
                    matching1[0] = XTree.DELETE
                    matching2[0] = XTree.DELETE
                    distance1 = dist[0][2] + dist[2][0]

                if (dist[1][1] < XTree.NO_CONNECTION):
                    matching1[1] = 1
                    matching2[1] = 1
                    distance1 += dist[1][1]
                else:
                    matching1[1] = XTree.DELETE
                    matching2[1] = XTree.DELETE
                    distance1 += dist[1][2] + dist[2][1]

                return distance1
            else:
                if (dist[0][1] < XTree.NO_CONNECTION):
                    matching1[0] = 1
                    matching2[1] = 0
                    distance2 = dist[0][1]
                else:
                    matching1[0] = XTree.DELETE
                    matching2[1] = XTree.DELETE
                    distance2 = dist[0][2] + dist[2][1]

                if (dist[1][0] < XTree.NO_CONNECTION):
                    matching1[1] = 0
                    matching2[0] = 1
                    distance2 += dist[1][0]
                else:
                    matching1[1] = XTree.DELETE
                    matching2[0] = XTree.DELETE
                    distance2 += dist[1][2] + dist[2][0]

                return distance2
        else:
            return self.optimalMatching(count1, count2, dist,
                           matching1, matching2)


    # Perform minimal-cost matching between two node lists
    # @param    count1    length of node list #1
    # @param    count2    length of node list #2
    # @param    dist    distance matrix
    # @param    matching1    matching list (for node list #1)
    # @param    matching2    matching list (for node list #2)
    # @return    distance

    def optimalMatching(self, count1, count2, dist, matching1, matching2):
        # Initialize matching.
        # Initial guess will be pair-matching between two lists.
        # Others will be insertion or deletion
        for i in range(count2):
            matching1[i] = i
        for i in range(count2, count1):
            matching1[i] = XTree.DELETE

        # Three artificial nodes: "start", "end" and "delete".
        count = count1 + count2 + 3

        # Initialize least cost matrix and path matrix.
        # Both have been initialized at the very beginning.

        # Start algorithm.
        while (True):
            # Construct least cost matrix.
            self.constructLCM(dist, matching1, count1, count2)

            # Initialize path matrix.
            for i in range(count):
                for j in range(count):
                    self._pathMatrix[i][j] = i

            # Search negative cost circuit.
            clen = self.searchNCC(count)
            if (clen > 0):
                # Modify matching.
                i = 0
                next_circuit = 0
                while (i < clen - 1):
                    n1 = self._circuit[next_circuit]
                    next_circuit = self._circuit[next_circuit+1]
                    # Node in node list 1.
                    if ((n1 > 0) and (n1 <= count1)):
                        nid1 = n1 - 1
                        nid2 = self._circuit[next_circuit] - count1 - 1
                        if (nid2 == count2):
                            nid2 = XTree.DELETE

                        matching1[nid1] = nid2
                    i += 1
            else: # Stop.
                break

        distance = 0
        # Suppose all insertion on list2
        for i in range(count2):
            matching2[i] = XTree.INSERT
            distance += dist[count1][i]

        # update distance by looking at matching pairs.
        for i in range(count1):
            mmm = matching1[i]
            if (mmm == XTree.DELETE):
                distance += dist[i][count2]
            else:
                matching2[mmm] = i
                distance += dist[i][mmm] - dist[count1][mmm]

        return distance


    # Construct a least cost matrix (of the flow network) based on
    # the cost matrix
    # @param    costMatrix    cost matrix
    # @param    matching    matching information
    # @param    nodeCount1    # of nodes in node list 1
    # @param    nodeCount2    # of nodes in node list 2

    def constructLCM(self, costMatrix, matching, nodeCount1, nodeCount2):
        # Three artificial nodes: "start", "end" and "delete".
        nodeCount = nodeCount1 + nodeCount2 + 3

        # Initialize.
        for i in range(nodeCount):
            for j in range(nodeCount):
                self._leastCostMatrix[i][j] = XTree.NO_CONNECTION

            # self.
            self._leastCostMatrix[i][i] = 0

        # Between start node and nodes in list 1.
        # Start -> node1 = Infinity; node1 -> Start = -0.
        for i in range(nodeCount1):
            self._leastCostMatrix[i+1][0] = 0

        # Between nodes in list2 and the end node.
        # Unless matched (later), node2 -> end = 0
        # end -> node2 = Infinity.
        for i in range(nodeCount2):
            self._leastCostMatrix[i+nodeCount1+1][nodeCount-1] = 0

        deleteCount = 0

        # Between nodes in list1 and nodes in list2.
        # For matched, node1 -> node2 = Infinity
        # node2 -> node1 = -1 * distance
        # For unmatched, node1 -> node2 = distance
        # node2 -> node1 = Infinity
        for i in range(nodeCount1):
            node1 = i + 1
            
            # According to cost matrix.
            for j in range(nodeCount2):
                node2 = j + nodeCount1 + 1
                self._leastCostMatrix[node1][node2] = costMatrix[i][j]

            # According to matching.
            if (matching[i] == XTree.DELETE):
                deleteCount += 1

                # node1 -> Delete = Infinity
                # Delete -> node1 = -1 * DELETE_COST
                self._leastCostMatrix[nodeCount-2][node1] = -1 * costMatrix[i][nodeCount2]
            else:
                node2 = matching[i] + nodeCount1 + 1

                # Between node1 and node2.
                self._leastCostMatrix[node1][node2] = XTree.NO_CONNECTION
                self._leastCostMatrix[node2][node1] = costMatrix[i][matching[i]] * -1

                # Between node1 and delete.
                self._leastCostMatrix[node1][nodeCount-2] = costMatrix[i][nodeCount2]

                # Between node2 and end.
                self._leastCostMatrix[node2][nodeCount-1] = XTree.NO_CONNECTION
                self._leastCostMatrix[nodeCount-1][node2] = costMatrix[nodeCount1][matching[i]]

        # Between the "Delete" and the "End".
        # If delete all, delete -> end = Infinity; end -> delete = 0.
        if (deleteCount == nodeCount1):
            self._leastCostMatrix[nodeCount-1][nodeCount-2] = 0
        # if no delete, delete -> end = 0; end -> delete = Infinity.
        elif (deleteCount == 0):
            self._leastCostMatrix[nodeCount-2][nodeCount-1] = 0
        # else, both 0
        else:
            self._leastCostMatrix[nodeCount-2][nodeCount-1] = 0
            self._leastCostMatrix[nodeCount-1][nodeCount-2] = 0


    # Search for negative cost circuit in the least cost matrix.
    # @param    nodeCount    node count
    # @return    the length of the path if found; otherwise 0
    def searchNCC(self, nodeCount):
        for k in range(nodeCount):
            for i in range(nodeCount):
                if ((i != k) and (self._leastCostMatrix[i][k] != XTree.NO_CONNECTION)):
                    for j in range(nodeCount):
                        if ((j != k) and (self._leastCostMatrix[k][j] != XTree.NO_CONNECTION)):
                            less = self._leastCostMatrix[i][k] + self._leastCostMatrix[k][j]
                            if (less < self._leastCostMatrix[i][j]):
                                self._leastCostMatrix[i][j] = less
                                self._pathMatrix[i][j] = k
                                
                                # Found!
                                if ((i == j) and (less < 0)):
                                    clen = 0 # the length of the circuit.
                                    
                                    # Locate the circuit.
                                    #circuit.addElement( Integer(i))
                                    self._circuit[0] = i
                                    self._circuit[1] = 2
                                    
                                    #circuit.addElement( Integer(pathMatrix[i][i]))
                                    self._circuit[2] = self._pathMatrix[i][i]
                                    self._circuit[3] = 4
                                    
                                    #circuit.addElement( Integer(i))
                                    self._circuit[4] = i
                                    self._circuit[5] = -1
                                    
                                    clen = 3
                                    
                                    finish = False 
                                    while (not finish):
                                        finish = True
                                        cit = 0
                                        n = 0
                                        while (cit < clen - 1):
                                            left = self._circuit[n]
                                            next_circ = self._circuit[n + 1]
                                            if next_circ == -1:
                                                right = -1
                                            else:
                                                right = self._circuit[next_circ]
                                            
                                            #int middle = pathMatrix[circuit[n-1]][circuit[n]]
                                            middle = self._pathMatrix[left][right]
                                            
                                            if (middle != left):
                                                #circuit.insert( cit, middle )
                                                self._circuit[clen * 2] = middle
                                                self._circuit[clen * 2 + 1] = next_circ
                                                self._circuit[n + 1] = clen * 2
                                                clen += 1
                                                
                                                finish = False
                                                break
                                            n = next_circ
                                            cit += 1
                                    
                                    return clen
                    
        return 0


    # For testing purpose -- print out matrixes
    def printMatrix(self, nodeCount):
        print "Cost Matrix:"
        for i in range(nodeCount):
            for j in range(nodeCount):
                if (self._leastCostMatrix[i][j] < XTree.NO_CONNECTION):
                    sys.stdout.write(self._leastCostMatrix[i][j] + "\t")
                else:
                    sys.stdout.write("\t")
            print

        print "\nPath Matrix:"
        for i in range(nodeCount):
            for j in range(nodeCount - 1):
                sys.stdout.write(self._pathMatrix[i][j] + "\t")
            print self._pathMatrix[i][nodeCount-1]


    # Write out the diff result -- how doc1 is changed to doc2
    # @param    input        the first/old xml document
    # @param    output        output file name
    # FIXME this is probably completely wrong ... IO is Java-specific!!!
    def writeDiff(self, inp, output):
        try:
            out = codecs.open(output, self._encoding)
            br =  open(inp)

            root1 = self._xtree1.getRoot()
            root2 = self._xtree2.getRoot()

            # XXX <root > is as valid as <root>,
            # but < root> is NOT!
            rootTag = "<" + self._xtree1.getTag(root1)
            line = br.readLine()
            while (line != None):
                if (line.indexOf(rootTag) >= 0):
                    break
                out.write(line + "\n")
                line = br.readLine()

            self._xtree1.getMatching(root1, self._matchp)
            if (self._matchp[0] == XTree.DELETE):
                self.writeDeleteNode(out, root1)
                self.writeInsertNode(out, root2)
            else:
                self.writeDiffNode(out, root1, root2)

            out.close()
        except IOError as (errno, strerror):
            print >>sys.stderr, "Exception: err no. %d\n%s" % (errno, strerror)

    # Write an element that has been deleted from the old document.
    # @param    out    output file writer
    # @param    node    element id

    def writeDeleteNode(self, out, node):
        if (self._xtree1.isElement(node)):
            tag = self._xtree1.getTag(node)
            out.write("<" + tag)

            # Attributes.
            attr = self._xtree1.getFirstAttribute(node)
            while (attr > 0):
                atag = self._xtree1.getTag(attr)
                value = self._xtree1.getAttributeValue(attr)
                out.write(" " + atag + "=\"" + value + "\"")
                attr = self._xtree1.getNextAttribute(attr)

            # Child nodes.
            child = self._xtree1.getFirstChild(node)

            if (child < 0):
                out.write("/><?DELETE " + tag + "?>\n")
                self._needNewLine = False
                return

            out.write("><?DELETE " + tag + "?>\n")
            self._needNewLine = False

            while (child > 0):
                self.writeMatchNode(out, self._xtree1, child)
                child = self._xtree1.getNextSibling(child)

            if (self._needNewLine):
                out.write("\n")
                self._needNewLine = False

            out.write("</" + tag + ">\n")
        else:
            out.write("<?DELETE \"" + self.constructText(self._xtree1, node) +
                  "\"?>\n")
            self._needNewLine = False


    # Write an element that has been inserted from the  document.
    # @param    out    output file writer
    # @param    node    element id

    def writeInsertNode(self, out, node):
        if (self._xtree2.isElement(node)):
            tag = self._xtree2.getTag(node)
            out.write("<" + tag)

            # Attributes.
            attr = self._xtree2.getFirstAttribute(node)
            while (attr > 0):
                atag = self._xtree2.getTag(attr)
                value = self._xtree2.getAttributeValue(attr)
                out.write(" " + atag + "=\"" + value + "\"")
                attr = self._xtree2.getNextAttribute(attr)

            # Child nodes.
            child = self._xtree2.getFirstChild(node)
            if (child < 0):
                out.write("/><?INSERT " + tag + "?>\n")
                self._needNewLine = False
                return

            out.write("><?INSERT " + tag + "?>\n")
            self._needNewLine = False

            while (child > 0):
                self.writeMatchNode(out, self._xtree2, child)
                child = self._xtree2.getNextSibling(child)

            if (self._needNewLine):
                out.write("\n")
                self._needNewLine = False

            out.write("</" + tag + ">\n")
        else:
            out.write(self.constructText(self._xtree2, node) +
                  "<?INSERT?>\n")
            self._needNewLine = False


    # Write an element that is unchanged or in a deleted node or in
    # an inserted node.
    # @param    out    output file writer
    # @param    xtree    the document tree
    # @param    node    element id

    def writeMatchNode(self, out, xtree, node):
        if (xtree.isElement(node)):
            tag = xtree.getTag(node)
            if (self._needNewLine):
                out.write("\n")

            out.write("<" + tag)

            # Attributes.
            attr = xtree.getFirstAttribute(node)
            while (attr > 0):
                atag = xtree.getTag(attr)
                value = xtree.getAttributeValue(attr)
                out.write(" " + atag + "=\"" + value + "\"")
                attr = xtree.getNextAttribute(attr)

            # Child nodes.
            child = xtree.getFirstChild(node)
            if (child < 0):
                out.write("/>\n")
                self._needNewLine = False
                return

            out.write(">")
            self._needNewLine = True

            while (child > 0):
                self.writeMatchNode(out, xtree, child)
                child = xtree.getNextSibling(child)

            if (self._needNewLine):
                out.write("\n")
                self._needNewLine = False

            out.write("</" + tag + ">\n")
        else:
            out.write(self.constructText(xtree, node))
            self._needNewLine = False


    # Write one node in the diff result.
    # @param    out    output file writer
    # @param    node1    the node in the first tree
    # @param    node2    node1's conterpart in the second tree

    def writeDiffNode(self, out, node1, node2):
        if (self._xtree1.isElement(node1)):
            tag = self._xtree1.getTag(node1)
            if (self._needNewLine):
                out.write("\n")
            out.write("<" + tag)

            # Attributes.
            attr1 = self._xtree1.getFirstAttribute(node1)
            diffff = ""
            while (attr1 > 0):
                atag = self._xtree1.getTag(attr1)
                value = self._xtree1.getAttributeValue(attr1)
                self._xtree1.getMatching(attr1, self._matchp)
                if (self._matchp[0] == XTree.MATCH):
                    out.write(" " + atag + "=\"" +
                          value + "\"")
                elif (self._matchp[0] == XTree.DELETE):
                    out.write(" " + atag + "=\"" +
                          value + "\"")
                    diffff += "<?DELETE " + atag + "?>"
                else:
                    value2 = self._xtree2.getAttributeValue(self._matchp[1])
                    out.write(" " + atag + "=\"" +
                          value2 + "\"")
                    diffff += "<?UPDATE " + atag + \
                          " FROM \"" + value + "\"?>"

                attr1 = self._xtree1.getNextAttribute(attr1)

            attr2 = self._xtree2.getFirstAttribute(node2)
            while (attr2 > 0):
                self._xtree2.getMatching(attr2, self._matchp)
                if (self._matchp[0] == XTree.INSERT):
                    atag = self._xtree2.getTag(attr2)
                    value = self._xtree2.getAttributeValue(attr2)
                    out.write(" " + atag + "=\"" +
                          value + "\"")
                    diffff += "<?INSERT " + atag + "?>"

                attr2 = self._xtree2.getNextAttribute(attr2)

            # Child nodes.
            child1 = self._xtree1.getFirstChild(node1)
            if (child1 < 0):
                out.write("/>" + diffff + "\n")
                self._needNewLine = False
                return

            out.write(">" + diffff)
            self._needNewLine = True

            while (child1 > 0):
                self._xtree1.getMatching(child1, self._matchp)
                if (self._matchp[0] == XTree.MATCH):
                    self.writeMatchNode(out, self._xtree1, child1)
                elif (self._matchp[0] == XTree.DELETE):
                    self.writeDeleteNode(out, child1)
                else:
                    self.writeDiffNode(out, child1, self._matchp[1])

                child1 = self._xtree1.getNextSibling(child1)

            child2 = self._xtree2.getFirstChild(node2)
            while (child2 > 0):
                self._xtree2.getMatching(child2, self._matchp)
                if (self._matchp[0] == XTree.INSERT):
                    self.writeInsertNode(out, child2)

                child2 = self._xtree2.getNextSibling(child2)

            if (self._needNewLine):
                out.write("\n")
                self._needNewLine = False

            out.write("</" + tag + ">\n")
        else:
            out.write(self.constructText(self._xtree2, node2) +
                  "<?UPDATE FROM \"" +
                  self.constructText(self._xtree1, node1) + "\"?>")
            self._needNewLine = False


    # Construct the text node -- to handle the possible CDATA sections.

    def constructText(self, xtree, eid):
        text = xtree.getText(eid)
        cdatalist = xtree.getCDATA(eid)
        if (cdatalist == None):
            return text

        buf =  ""
        count = cdatalist.size()
        lastEnd = 0

        for i in range(0,count,2):
            cdataStart = int(cdatalist[i])
            cdataEnd = int(cdatalist[i+1])

            if (cdataStart > lastEnd):
                buf += text[lastEnd:cdataStart]
            buf += "<![CDATA[" + text[cdataStart:cdataEnd] + "]]>"
            lastEnd = cdataEnd
        if (lastEnd < len(text)):
            buf += text[lastEnd:]

        return str(buf)

def readParameters(args, params):
    opid = 0
    if (len(args) < 3):
        return False
    # we are not in the object, so how can we get to these values?
    # FIXME global module variables?
    elif (args[0] == "-o"):
        _oFlag = True
        opid += 1
    elif (args[0] == "-g"):
        _gFlag = True
        opid += 1

    if (args[opid] == "-p"):
        opid += 1
        p = 0
#        try:
        p = float(args[opid])
        opid += 1
# FIXME ... most likely FloatingPointError
#        except NumberFormatException:
#            return False

        if ((p <= 0) or (p > 1)):
            return False
        XDiff._NO_MATCH_THRESHOLD = p

    if (args[opid] == "-e"):
        opid += 1
        _encoding = args[opid]
        opid += 1

    if ((len(args) - opid) != 3):
        return False
    params.append(args[opid])
    opid += 1
    params.append(args[opid])
    opid += 1
    params.append(args[opid])

    return True

if __name__ == "__main__":
    parameters =  []
    if (not readParameters(sys.argv, parameters)):
        print >>sys.stderr, __doc__
        sys.exit(1)

    mydiff =  XDiff(parameters[0], parameters[1], parameters[2])
