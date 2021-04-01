Extension { #name : #MacOSXPlatform }

{ #category : #'*PhaNAPI-Core' }
MacOSXPlatform >> dynamicLibraryPrefix [
	^ 'lib'
]

{ #category : #'*PhaNAPI-Core' }
MacOSXPlatform >> dynamicLibrarySuffix [
	^ '.dylib'
]

{ #category : #'*PhaNAPI-Core' }
MacOSXPlatform >> phanapiPlatformName [
	^ 'osx-' , self phanapiArchitectureName
]
