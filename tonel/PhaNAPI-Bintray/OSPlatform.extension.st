Extension { #name : #OSPlatform }

{ #category : #'*PhaNAPI-Bintray' }
OSPlatform >> bintrayArchitectureName [
	self flag: 'TODO: Add support for ARM.'.
	
	Smalltalk wordSize = 4 ifTrue: [ 
		^ 'x86'
	] ifFalse: [ 
		^ 'x64'
	]
]
