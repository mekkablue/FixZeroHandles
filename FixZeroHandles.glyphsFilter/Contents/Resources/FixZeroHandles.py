#!/usr/bin/env python
# encoding: utf-8

import objc
from Foundation import *
from AppKit import *
import sys, os, re

MainBundle = NSBundle.mainBundle()
path = MainBundle.bundlePath() + "/Contents/Scripts"
if not path in sys.path:
	sys.path.append( path )

import GlyphsApp

GlyphsFilterProtocol = objc.protocolNamed( "GlyphsFilter" )

class GlyphsFilterFixZeroHandles ( NSObject, GlyphsFilterProtocol ):
	tunnifyLo = 0.43
	tunnifyHi = 0.73
	
	def init( self ):
		"""
		Do all initializing here.
		"""
		return self
	
	def interfaceVersion( self ):
		"""
		Distinguishes the API version the plugin was built for. 
		Return 1.
		"""
		return 1
	
	def setController_( self, Controller ):
		"""
		Do not touch this.
		"""
		try:
			self._controller = Controller
		except Exception as e:
			self.logToConsole( "setController_: %s" % str(e) )
	
	def controller( self ):
		"""
		Do not touch this.
		"""
		try:
			return self._controller
		except Exception as e:
			self.logToConsole( "controller: %s" % str(e) )
		
	def setup( self ):
		"""
		Do not touch this.
		"""
		try:
			return None
		except Exception as e:
			self.logToConsole( "setup: %s" % str(e) )
	
	def title( self ):
		"""
		This is the human-readable name as it appears in the menu.
		"""
		return "Fix Zero Handles"
	
	def keyEquivalent( self ):
		""" 
		The key together with Cmd+Shift will be the shortcut for the filter.
		Return None if you do not want to set a shortcut.
		Users can set their own shortcuts in System Prefs.
		"""
		return None
	
	def processLayer( self, thisLayer, selectionCounts ):
		"""
		Each selected layer is processed here.
		"""
		try:
			selection = thisLayer.selection()
			if selection == (): #empty selection
				selectionCounts = False
			
			for thisPath in thisLayer.paths:
				numOfNodes = len( thisPath.nodes )
				nodeIndexes = range( numOfNodes )
		
				for i in nodeIndexes:
					thisNode = thisPath.nodes[i]
			
					if (thisNode in selection or not selectionCounts) and thisNode.type == 65:
						if thisPath.nodes[i-1].type == 65:
							segmentNodeIndexes = [ i-2, i-1, i, i+1 ]
						else:
							segmentNodeIndexes = [ i-1, i, i+1, i+2 ]
				
						for x in range(len(segmentNodeIndexes)):
							segmentNodeIndexes[x] = segmentNodeIndexes[x] % numOfNodes
				
						thisSegment = [ [n.x, n.y] for n in [ thisPath.nodes[i] for i in segmentNodeIndexes ] ]
						newHandles = self.tunnify( thisSegment )
						if newHandles:
							xHandle1, yHandle1, xHandle2, yHandle2 = newHandles
							thisPath.nodes[ segmentNodeIndexes[1] ].x = xHandle1
							thisPath.nodes[ segmentNodeIndexes[1] ].y = yHandle1
							thisPath.nodes[ segmentNodeIndexes[2] ].x = xHandle2
							thisPath.nodes[ segmentNodeIndexes[2] ].y = yHandle2
			return True
		except Exception as e:
			self.logToConsole( "processLayer: %s" % str(e) )
			return False
	
	def xyAtPercentageBetweenTwoPoints( self, firstPoint, secondPoint, percentage ):
		"""
		Returns the x, y for the point at percentage
		(where 100 percent is represented as 1.0)
		between NSPoints firstPoint and secondPoint.
		"""
		x = firstPoint.x + percentage * ( secondPoint.x - firstPoint.x )
		y = firstPoint.y + percentage * ( secondPoint.y - firstPoint.y )
		return x, y
	
	def tunnify( self, segment ):
		"""
		Calculates the average curvature for Bezier curve segment P1, P2, P3, P4,
		and returns new values for P2, P3.
		"""
		try:
			x1, y1 = segment[0]
			x2, y2 = segment[1]
			x3, y3 = segment[2]
			x4, y4 = segment[3]
			
			if [x1, y1] == [x2, y2]:
				xInt, yInt = x3, y3
				firstHandlePercentage = self.tunnifyLo
				secondHandlePercentage = self.tunnifyHi
			elif [x3, y3] == [x4, y4]:
				xInt, yInt = x2, y2
				firstHandlePercentage = self.tunnifyHi
				secondHandlePercentage = self.tunnifyLo
			else:
				# no zero handle
				return False
			
			intersectionPoint = NSPoint( xInt, yInt )
			segmentStartPoint = NSPoint( x1, y1 )
			segmentFinalPoint = NSPoint( x4, y4 )
			
			firstHandleX, firstHandleY = self.xyAtPercentageBetweenTwoPoints( segmentStartPoint, intersectionPoint, firstHandlePercentage )
			secondHandleX, secondHandleY = self.xyAtPercentageBetweenTwoPoints( segmentFinalPoint, intersectionPoint, secondHandlePercentage )
			
			return firstHandleX, firstHandleY, secondHandleX, secondHandleY
		except Exception as e:
			self.logToConsole( "tunnify: %s" % str(e) )
	
	def runFilterWithLayers_error_( self, Layers, Error ):
		"""
		Invoked when user triggers the filter through the Filter menu
		and more than one layer is selected.
		"""
		try:
			for k in range(len(Layers)):
				Layer = Layers[k]
				Layer.clearSelection()
				self.processLayer( Layer, False )
		except Exception as e:
			self.logToConsole( "runFilterWithLayers_error_: %s" % str(e) )
	
	def runFilterWithLayer_options_error_( self, Layer, Options, Error ):
		"""
		Required for compatibility with Glyphs version 702 or later.
		Leave this as it is.
		"""
		try:
			return self.runFilterWithLayer_error_( self, Layer, Error )
		except Exception as e:
			self.logToConsole( "runFilterWithLayer_options_error_: %s" % str(e) )
	
	def runFilterWithLayer_error_( self, Layer, Error ):
		"""
		Invoked when user triggers the filter through the Filter menu
		and only one layer is selected.
		"""
		try:
			return self.processLayer( Layer, True )
		except Exception as e:
			self.logToConsole( "runFilterWithLayer_error_: %s" % str(e) )
	
	def processFont_withArguments_( self, Font, Arguments ):
		"""
		Invoked when called as Custom Parameter in an instance at export.
		The Arguments come from the custom parameter in the instance settings. 
		The first item in Arguments is the class-name. After that, it depends on the filter.
		"""
		try:
			# set glyphList to all glyphs
			glyphList = Font.glyphs
			
			# Override defaults with actual values from custom parameter:
			if len( Arguments ) > 1:
				
				# change glyphList to include or exclude glyphs
				if "exclude:" in Arguments[-1]:
					excludeList = [ n.strip() for n in Arguments.pop(-1).replace("exclude:","").strip().split(",") ]
					glyphList = [ g for g in glyphList if not g.name in excludeList ]
				elif "include:" in Arguments[-1]:
					includeList = [ n.strip() for n in Arguments.pop(-1).replace("include:","").strip().split(",") ]
					glyphList = [ Font.glyphs[n] for n in includeList ]
			
			FontMasterId = Font.fontMasterAtIndex_(0).id
			for thisGlyph in glyphList:
				Layer = thisGlyph.layerForKey_( FontMasterId )
				self.processLayer( Layer, False )
		except Exception as e:
			self.logToConsole( "processFont_withArguments_: %s" % str(e) )
	
	def logToConsole( self, message ):
		"""
		The variable 'message' will be passed to Console.app.
		Use self.logToConsole( "bla bla" ) for debugging.
		"""
		myLog = "Filter %s:\n%s" % ( self.title(), message )
		NSLog( myLog )
