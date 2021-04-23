Extension { #name : #OSPlatform }

{ #category : #'*PhaNAPI-Core' }
OSPlatform >> dynamicLibraryPrefix [
	^ ''
]

{ #category : #'*PhaNAPI-Core' }
OSPlatform >> dynamicLibrarySuffix [
	^ ''
]

{ #category : #'*PhaNAPI-Core' }
OSPlatform >> phanapiArchitectureName [
	self flag: 'TODO: Add support for ARM.'.
	
	Smalltalk wordSize = 4 ifTrue: [ 
		^ 'x86'
	] ifFalse: [ 
		^ 'x64'
	]
]
