Extension { #name : #WinPlatform }

{ #category : #'*PhaNAPI-Core' }
WinPlatform >> dynamicLibrarySuffix [
	^ '.dll'
]

{ #category : #'*PhaNAPI-Core' }
WinPlatform >> phanapiPlatformName [
	^ 'windows-' , self phanapiArchitectureName
]
