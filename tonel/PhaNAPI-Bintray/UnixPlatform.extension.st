Extension { #name : #UnixPlatform }

{ #category : #'*PhaNAPI-Bintray' }
UnixPlatform >> bintrayPlatformName [
	(self version beginsWith: 'linux') ifTrue: [ 
		^ 'linux-' , self bintrayArchitectureName
	].

	^ 'unix-' , self bintrayArchitectureName
]
