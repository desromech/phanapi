"
I am an utility that provides an unique session object for supporting the Smalltalk session pattern in Squeak.
"
Class {
	#name : #PhaNAPISqueakSession,
	#superclass : #Object,
	#classVars : [
		'UniqueSessionObject'
	],
	#category : #'PhaNAPI-Squeak'
}

{ #category : #'system startup' }
PhaNAPISqueakSession class >> initialize [
	Smalltalk addToStartUpList: self.
	Smalltalk addToShutDownList: self.
]

{ #category : #accessing }
PhaNAPISqueakSession class >> session [
	^ UniqueSessionObject ifNil: [ UniqueSessionObject := Object new ]
]

{ #category : #'system startup' }
PhaNAPISqueakSession class >> startUp [
	UniqueSessionObject := Object new.
]
