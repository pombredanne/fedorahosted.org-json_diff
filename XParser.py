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
# SERVICES LOSS OF USE, DATA, OR PROFITS OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING
# IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import XTree
import sys, hashlib
import xml.sax
_STACK_SIZE = 100

class ErrorHandler:
    """Basic interface for SAX error handlers. If you create an object
    that implements this interface, then register the object with your
    Parser, the parser will call the methods in your object to report
    all warnings and errors. There are three levels of errors
    available: warnings, (possibly) recoverable errors, and
    unrecoverable errors. All methods take a SAXParseException as the
    only parameter."""
    
    

    def error(self, exception):
        "Handle a recoverable error."
        sys.stderr.write ("Error: %s\n" % exception)

    def fatalError(self, exception):
        "Handle a non-recoverable error."
        sys.stderr.write ("Fatal error: %s\n" % exception)
        raise xml.sax.SAXParseException

    def warning(self, exception):
        "Handle a warning."
        sys.stderr.write ("Warning: %s\n" % exception)

# This is interesting
# http://www.virtuousprogrammer.com/?page_id=183
# http://docs.python.org/library/xml.sax.reader.html
# <code>XParser</code> parses an input XML document and constructs an
# <code>XTree</code>
# class XParser extends DefaultHandler implements LexicalHandler
class XParser(xml.sax.handler.ContentHandler):
#    private XMLReader    self._parser
#    private XTree        self._xtree
#    private int        self._idStack[], self._lsidStack[] # id and left sibling
#    private long        self._valueStack[]
#    private int        self._stackTop, self._currentNodeID
#    private boolean        self._readElement
#    private StringBuffer    self._elementBuffer

# Constructor.
    def __init__(self):
        xml.sax.handler.ContentHandler.__init__(self)
        self._setValidation = False
        self._setNameSpaces = True
        self._setSchemaSupport = True
        self._setSchemaFullSupport = False
        self._setNameSpacePrefixes = True
        self._readElement = False
        self._xtree = None

#        try:
        self._parser = xml.sax.make_parser()
        self._parser.setFeature(xml.sax.handler.feature_validation, \
            self._setValidation)
        self._parser.setFeature(xml.sax.handler.feature_namespaces, \
            self._setNameSpaces)
        self._parser.setFeature(xml.sax.handler.feature_namespace_prefixes, \
            self._setNameSpacePrefixes)
        #self._parser.setFeature("http://apache.org/xml/features/validation/schema", \
        #    self._setSchemaSupport)
        #self._parser.setFeature("http://apache.org/xml/features/validation/schema-full-checking", \
        #    self._setSchemaFullSupport)

        self._parser.setContentHandler(self)
#            self._parser.setErrorHandler(self)
        self._parser.setProperty(xml.sax.handler.property_lexical_handler, self)
#        except xml.sax.SAXParseException as (errno, strerror): # swallowing exception FIXME
#            print >>sys.stderr, "Exception: err no. %d\n%s" % (errno, strerror)
#            sys.exit(1)

        self._idStack = []
        self._lsidStack = []
        self._valueStack = []
        self._stackTop = 0
        self._currentNodeID = XTree.NULL_NODE
        self._elementBuffer = ""

# Parse an XML document
# @param    uri    input XML document
# @return    the created XTree
    def parse(self, uri):
        self._xtree = XTree.XTree()
        self._idStack.append(XTree.NULL_NODE)
        self._lsidStack.append(XTree.NULL_NODE)

#        try:
        self._parser.parse(uri)
#        except xml.sax.SAXParseException as (errno, strerror):
#            print >>sys.stderr, "Exception: err no. %d\n%s" % (errno, strerror)
#            sys.exit(1)

        return self._xtree

    # Document handler methods

    def startElement(self, local, attrs):
        # if text is mixed with elements
        if (len(self._elementBuffer) > 0):
            text = str(self._elementBuffer).strip()
            if (len(text) > 0):
                # Original Java has long here, we have str. FIXME
                value = hashlib.sha1(text).digest()
                tid = self._xtree.addText(self._idStack[self._stackTop], self._lsidStack[self._stackTop], text, value)
                self._lsidStack[self._stackTop] = tid
                self._currentNodeID = tid
                self._valueStack[self._stackTop] += value

        eid = self._xtree.addElement(self._idStack[self._stackTop],
                        self._lsidStack[self._stackTop], local)

        # Update last sibling info.
        self._lsidStack[self._stackTop] = eid

        # Push
        self._stackTop += 1
        self._idStack[self._stackTop] = eid
        self._currentNodeID = eid
        self._lsidStack[self._stackTop] = XTree.NULL_NODE
        self._valueStack[self._stackTop] = hashlib.sha1(local).digest()

        # Take care of attributes
        if ((attrs != None) and (attrs.getLength() > 0)):
            for i in range(attrs.getLength()):
                name = attrs.getQName(i)
                value = attrs.getValue(i)
                namehash = hashlib.sha1(name).digest()
                valuehash = hashlib.sha1(value).digest()
                attrhash = namehash * namehash + \
                           valuehash * valuehash
                aid = self._xtree.addAttribute(eid, self._lsidStack[self._stackTop], name, value, namehash, attrhash)

                self._lsidStack[self._stackTop] = aid
                self._currentNodeID = aid + 1
                self._valueStack[self._stackTop] += attrhash * attrhash

        self._readElement = True
        self._elementBuffer = ""
 
    def characters(self, ch):
        self._elementBuffer += ch

    def endElement(self, name):
        if (self._readElement):
            if (len(self._elementBuffer) > 0):
                text = str(self._elementBuffer)
                value = hashlib.sha1(text).digest()
                self._currentNodeID = \
                    self._xtree.addText(self._idStack[self._stackTop],
                               self._lsidStack[self._stackTop],
                               text, value)
                self._valueStack[self._stackTop] += value
            else:    # an empty element
                self._currentNodeID = \
                    self._xtree.addText(self._idStack[self._stackTop], \
                               self._lsidStack[self._stackTop], \
                               "", 0)
            self._readElement = False
        else:
            if (len(self._elementBuffer) > 0):
                text = str(self._elementBuffer).strip()
                # More text nodes before end of the element.
                if (len(text) > 0):
                    value = hashlib.sha1(text).digest()
                    self._currentNodeID = \
                      self._xtree.addText(self._idStack[self._stackTop], \
                             self._lsidStack[self._stackTop], \
                             text, value)
                    self._valueStack[self._stackTop] += value

        self._elementBuffer = ""
        self._xtree.addHashValue(self._idStack[self._stackTop],
                    self._valueStack[self._stackTop])
        self._valueStack[self._stackTop-1] += self._valueStack[self._stackTop] * \
                        self._valueStack[self._stackTop]
        self._lsidStack[self._stackTop-1] = self._idStack[self._stackTop]

        # Pop
        self._stackTop -= 1

    # End of document handler methods

    # Lexical handler methods.

    def startCDATA(self):
        # The text node id should be the one next to the current
        # node id.
        textid = self._currentNodeID + 1
        text = str(self._elementBuffer)
        self._xtree.addCDATA(textid, len(text))

    def endCDATA(self):
        textid = self._currentNodeID + 1
        text = str(self._elementBuffer)
        self._xtree.addCDATA(textid, len(text))

    # Following functions are not implemented.
    def comment(self, ch):
        pass
    
    def startDTD(self, name, publicId, systemId):
        pass

    def endDTD(self):
        pass

    def startEntity(self, name):
        pass

    def endEntity(self, name):
        pass
    
    # End of lexical handler methods.

