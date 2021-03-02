/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/explicit-module-boundary-types */
/* eslint-disable @typescript-eslint/no-unsafe-assignment */
/* eslint-disable @typescript-eslint/no-unsafe-member-access */
import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';

@Component({
  templateUrl: 'confirm-dialog.component.html',
  styleUrls: ['confirm-dialog.component.scss'],
})
export class ConfirmDialogComponent implements OnInit {
  dialog: any;
  hideCancelButton: boolean;
  confirmButtonText: string;
  cancelButtonText: string;

  constructor(@Inject(MAT_DIALOG_DATA) private data) {
    this.hideCancelButton = this.data.hideCancelButton && true;

    if (data.confirmButtonText) {
      this.confirmButtonText = data.confirmButtonText;
    } else {
      this.confirmButtonText = this.hideCancelButton ? 'Close' : 'Confirm';
    }

    this.cancelButtonText = data.cancelButtonText || 'Cancel';
  }

  ngOnInit(): void {
    this.dialog = this.data;
  }
}
