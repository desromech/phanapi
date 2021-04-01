Extension { #name : #UnixPlatform }

{ #category : #'*PhaNAPI-Core' }
UnixPlatform >> dynamicLibraryPrefix [
	^ 'lib'
]

{ #category : #'*PhaNAPI-Core' }
UnixPlatform >> dynamicLibrarySuffix [
	^ '.so'
]

{ #category : #'*PhaNAPI-Core' }
UnixPlatform >> phanapiPlatformName [
	(self version beginsWith: 'linux') ifTrue: [ 
		^ 'linux-' , self phanapiArchitectureName
	].

	^ 'unix-' , self phanapiArchitectureName
]
