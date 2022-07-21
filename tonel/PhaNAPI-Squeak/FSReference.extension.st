Extension { #name : #FSReference }

{ #category : #'*PhaNAPI-Squeak' }
FSReference >> binaryReadStreamDo: aBlock [
	"Evaluate aBlock with an FSReadStream on myself. 
	Note this will not create a new file it does not exist already"
	| stream |
	stream := self readStream.
	stream binary
	^ [ aBlock value: stream ] ensure: [ stream close ]
]
