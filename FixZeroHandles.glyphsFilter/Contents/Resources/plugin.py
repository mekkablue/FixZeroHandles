# encoding: utf-8

import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from math import atan2, sqrt

def angle(p0, p1):
	return atan2(p1[1] - p0[1], p1[0] - p0[0])

def distance(p0, p1):
	return sqrt((p0[0] - p1[0]) ** 2 + (p0[1] - p1[1]) ** 2)

class FixZeroHandles(FilterWithoutDialog):
	tunnifyLo = 0.43
	tunnifyHi = 0.73
	
	def settings(self):
		self.menuName = Glyphs.localize({
			'en': u'Fix Zero Handles',
			'de': u'Null-Anfasser beheben',
			'fr': u'Corriger les poignées rétractées',
			'es': u'Corregir manejadores cero',
			'zh': u'🍭修正单摇臂',
		})
		self.keyboardShortcut = None # With Cmd+Shift

	def filter(self, thisLayer, inEditView, customParameters):
		selection = thisLayer.selection
		
		if inEditView and selection:
			selectionCounts = True
		else:
			selectionCounts = False
		
		thisCompString = thisLayer.compareString()
		for j, thisPath in enumerate(thisLayer.paths):
			numOfNodes = len( thisPath.nodes )
			nodeIndexes = range( numOfNodes )
			handleIndexesToBeRemoved = []
	
			for i in nodeIndexes:
				thisNode = thisPath.nodes[i]
		
				if (thisNode in selection or not selectionCounts) and thisNode.type == GSOFFCURVE:
					if thisPath.nodes[i-1].type == GSOFFCURVE:
						segmentNodeIndexes = [ i-2, i-1, i, i+1 ]
					else:
						segmentNodeIndexes = [ i-1, i, i+1, i+2 ]
			
					for x in range(len(segmentNodeIndexes)):
						segmentNodeIndexes[x] = segmentNodeIndexes[x] % numOfNodes
			
					thisSegment = [ (n.x, n.y) for n in [ thisPath.nodes[i] for i in segmentNodeIndexes ] ]
					
					# Check for the same segment in other layers
					
					otherLayerSegments = []
					thisGlyph = thisLayer.parent
					if thisGlyph:
						for otherLayer in [l for l in thisGlyph.layers if l.compareString() == thisCompString]:
							otherLayerSegments.append([ (n.x, n.y) for n in [ otherLayer.paths[j].nodes[i] for i in segmentNodeIndexes ] ])
						segmentTypes = [self.isLineOrShouldBeLine( s ) for s in otherLayerSegments]
						#print segmentTypes
						newHandles = self.tunnify( thisSegment )
						if newHandles != False:
							if newHandles == True:
								if all(segmentTypes):
									# segment is a "quasi-line" in all layers, remove handles
									handleIndexesToBeRemoved.append( segmentNodeIndexes[1] )
								else:
									newHandles = self.getQuasiLineHandles( thisSegment )
									xHandle1, yHandle1, xHandle2, yHandle2 = newHandles
									thisPath.nodes[ segmentNodeIndexes[1] ].x = xHandle1
									thisPath.nodes[ segmentNodeIndexes[1] ].y = yHandle1
									thisPath.nodes[ segmentNodeIndexes[2] ].x = xHandle2
									thisPath.nodes[ segmentNodeIndexes[2] ].y = yHandle2
							else:
								xHandle1, yHandle1, xHandle2, yHandle2 = newHandles
								thisPath.nodes[ segmentNodeIndexes[1] ].x = xHandle1
								thisPath.nodes[ segmentNodeIndexes[1] ].y = yHandle1
								thisPath.nodes[ segmentNodeIndexes[2] ].x = xHandle2
								thisPath.nodes[ segmentNodeIndexes[2] ].y = yHandle2
			
			if handleIndexesToBeRemoved:
				for thisHandleIndex in list(set(handleIndexesToBeRemoved))[::-1]:
					try:
						thisGlyph = thisLayer.parent
						if thisGlyph:
							for layer in thisGlyph.layers:
								if layer.paths[j].nodes[thisHandleIndex].type == GSOFFCURVE:
									layer.paths[j].removeNodeCheck_( layer.paths[j].nodes[thisHandleIndex] )
					except:
						print "Warning: Could not convert into straight segment in %s. Please report on: \nhttps://github.com/mekkablue/FixZeroHandles/issues\nThanks." % thisGlyph.name
	
	def __file__(self):
		"""Please leave this method unchanged"""
		return __file__
	
	def getBestPoint( self, points, orig_pt, ref_pt0, ref_pt1):
		# Select the point from a list of float coordinates that will round to the grid the best.
		
		points.append(orig_pt)
		
		# Choose the sum of the difference of x and y coordinate
		# This is the simplest method
		#error_points = zip([abs(p[0] - round(p[0])) + abs(p[1] - round(p[1])) for p in points], points)
		
		# Minimize the distance between the rounded point and the free point
		#error_points = zip([distance(p, (round(p[0]), round(p[1]))) for p in points], points)
		
		# Minimize the angle deviation from the angle between ref_pt0 and ref_pt1
		ref_angle = angle(ref_pt0, ref_pt1)
		if ref_angle == angle(ref_pt0, (round(orig_pt[0]), round(orig_pt[1]))):
			return orig_pt
		else:
			error_points = zip(
				[
					abs(ref_angle - angle(ref_pt0, (round(p[0]), round(p[1])))) for p in points
				],
				points
			)
		
		#print "Errors with point:", error_points
		return sorted(error_points)[0][1]
	
	def xyAtPercentageBetweenTwoPoints( self, firstPoint, secondPoint, percentage, allowedHandleLengthError = 0 ):
		"""
		Returns the x, y for the point at percentage
		(where 100 percent is represented as 1.0)
		between NSPoints firstPoint and secondPoint.
		"""
		x = firstPoint.x + percentage * ( secondPoint.x - firstPoint.x )
		y = firstPoint.y + percentage * ( secondPoint.y - firstPoint.y )
		if allowedHandleLengthError > 0:
			#print "Optimizing handle length ..."
			#print firstPoint, secondPoint
			min_percentage = percentage - 0.5 * percentage * allowedHandleLengthError
			max_percentage = percentage + 0.5 * percentage * allowedHandleLengthError
			#print "Minimum percentage:", min_percentage
			#print "Maximum percentage:", max_percentage
			min_pt = self.xyAtPercentageBetweenTwoPoints( firstPoint, secondPoint, min_percentage)
			max_pt = self.xyAtPercentageBetweenTwoPoints( firstPoint, secondPoint, max_percentage)
			sample_count = 2 * int(round(distance(min_pt, max_pt)))
			#print "Number of samples:", sample_count
			if sample_count > 0:
				step = allowedHandleLengthError / float(sample_count)
				test_percentages = itertools.islice(itertools.count(min_percentage, step), sample_count)
				points = [self.xyAtPercentageBetweenTwoPoints( firstPoint, secondPoint, p) for p in test_percentages]
				#print points
				xo, yo = self.getBestPoint(points, (x, y), (firstPoint.x, firstPoint.y), (secondPoint.x, secondPoint.y))
				#print "Optimized: (%0.3f, %0.3f) -> (%0.3f, %0.3f)" % (x, y, xo, yo)
				x = xo
				y = yo
		return x, y
	
	def tunnify( self, segment ):
		"""
		Calculates the average curvature for Bezier curve segment P1, P2, P3, P4,
		and returns new values for P2, P3.
		"""
		x1, y1 = segment[0]
		x2, y2 = segment[1]
		x3, y3 = segment[2]
		x4, y4 = segment[3]
		
		if (x1, y1) == (x2, y2):
			if (x3, y3) == (x4, y4):
				return True
			xInt, yInt = x3, y3
			firstHandlePercentage = self.tunnifyLo
			secondHandlePercentage = self.tunnifyHi
		elif (x3, y3) == (x4, y4):
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
	
	def isLineOrShouldBeLine( self, segment ):
		#print "Check Segment type:", segment
		if len(segment) == 2:
			#print "Real line"
			return True
		if len(segment) == 4:
			x1, y1 = segment[0]
			x2, y2 = segment[1]
			x3, y3 = segment[2]
			x4, y4 = segment[3]
			
			if (x1, y1) == (x2, y2):
				if (x3, y3) == (x4, y4):
					#print "Quasi line"
					return True
		return False
	
	def getQuasiLineHandles( self, segment ):
		x1, y1 = segment[0]
		x2, y2 = segment[1]
		x3, y3 = segment[2]
		x4, y4 = segment[3]
		
		segmentStartPoint = NSPoint( x1, y1 )
		segmentFinalPoint = NSPoint( x4, y4 )
		
		firstHandleX,  firstHandleY  = self.xyAtPercentageBetweenTwoPoints( segmentStartPoint, segmentFinalPoint, 0.333333, allowedHandleLengthError = 0.075 )
		secondHandleX, secondHandleY = self.xyAtPercentageBetweenTwoPoints( segmentStartPoint, segmentFinalPoint, 0.666667, allowedHandleLengthError = 0.075 )
		
		return firstHandleX, firstHandleY, secondHandleX, secondHandleY
	