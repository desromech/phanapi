Extension { #name : #SmalltalkImage }

{ #category : #'*PhaNAPI-Squeak' }
SmalltalkImage >> session [
	^ self at: #DoItFirst ifPresent: [:cls | cls current] ifAbsent: [PhaNAPISqueakSession session]
]
