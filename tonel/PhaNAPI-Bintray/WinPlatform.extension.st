Extension { #name : #WinPlatform }

{ #category : #'*PhaNAPI-Bintray' }
WinPlatform >> bintrayPlatformName [
	^ 'windows-' , self bintrayArchitectureName
]
