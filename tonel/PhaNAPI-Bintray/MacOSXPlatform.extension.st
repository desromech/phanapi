Extension { #name : #MacOSXPlatform }

{ #category : #'*PhaNAPI-Bintray' }
MacOSXPlatform >> bintrayPlatformName [
	^ 'osx-' , self bintrayArchitectureName
]
