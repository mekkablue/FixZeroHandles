# FixZeroHandles.glyphsFilter

This is a plugin for the [Glyphs font editor](http://glyphsapp.com/) by Georg Seifert. It analyzes the path structure of selected layers and will rearrange path segments that contain completely retracted handles, a.k.a. ‘zero handles’. Zero handles typically appear in outlines imported from other vector apps, such as Adobe Illustrator. Zero handles are considered bad style, or even an error, and can cause a range of problems, especially when you are trying to convert your outlines to  TrueType curves.

![Fixing Zero Handles: Before and After.](FixZeroHandles.png "Fix Zero Handles")

Installation of this filter will add the menu item *Filter > Fix Zero Handles*. You can set a keyboard shortcut in System Preferences.

### Installation

1. Download the complete ZIP file and unpack it, or clone the repository.
2. Double click the .glyphsFilter file. Confirm the dialog that appears in Glyphs.
3. Restart Glyphs

### Usage Instructions

1. Open a glyph in Edit View, or select any number of glyphs in Font or Edit View.
2. Choose *Filter > Fix Zero Handles*.

Alternatively, you can also use it as a custom parameter in an instance:

	Property: Filter
	Value: GlyphsFilterFixZeroHandles;

At the end of the parameter value, you can hang `exclude:` or `include:`, followed by a comma-separated list of glyph names. This will apply the filter only to the included glyphs, or the glyphs not excluded, respectively.

### Requirements

The plugin needs Glyphs 1.4.3 or higher, running on OS X 10.7 or later. I can only test it in current OS versions, and I assume it will not work in versions of Mac OS X older than 10.7.

### License

Copyright 2014 Rainer Erich Scheichelbauer (@mekkablue).
Based on sample code by Georg Seifert (@schriftgestalt).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

See the License file included in this repository for further details.
