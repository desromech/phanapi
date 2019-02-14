Extension { #name : #WinPlatform }

{ #category : #'*PhaNAPI-Bintray' }
WinPlatform >> bintrayArchitectureName [
	Smalltalk wordSize = 8 ifTrue: [ ^ 'x64' ].
	^ super bintrayArchitectureName
]

{ #category : #'*PhaNAPI-Bintray' }
WinPlatform >> bintrayPlatformName [
	^ 'windows-' , self bintrayArchitectureName
]
