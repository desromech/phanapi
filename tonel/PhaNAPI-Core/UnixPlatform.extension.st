Extension { #name : #UnixPlatform }

{ #category : #'*PhaNAPI-Core' }
UnixPlatform >> dynamicLibraryPrefix [
	^ 'lib'
]

{ #category : #'*PhaNAPI-Core' }
UnixPlatform >> dynamicLibrarySuffix [
	^ '.so'
]
