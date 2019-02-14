Extension { #name : #MacOSXPlatform }

{ #category : #'*PhaNAPI-Core' }
MacOSXPlatform >> dynamicLibraryPrefix [
	^ 'lib'
]

{ #category : #'*PhaNAPI-Core' }
MacOSXPlatform >> dynamicLibrarySuffix [
	^ '.dylib'
]
